import asyncio
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

RAG_PREFIX = "smart_agent:rag:"
RAG_DOC_IDS_KEY = f"{RAG_PREFIX}doc_ids"


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))


def _chunk_text(text: str, chunk_size: int = 1200, overlap: int = 120) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    step = max(1, chunk_size - overlap)
    while start < len(text):
        chunk = text[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks


class FalkorGraphRAGService:
    """
    FalkorDB-backed RAG service.

    This keeps the existing async API expected by agent nodes, but persists
    indexed text chunks in FalkorDB (Redis protocol) so it aligns with the
    Graphiti + Falkor deployment model.
    """

    def __init__(self):
        self._redis = None

    async def initialize(self):
        from app.database.connection import get_redis

        self._redis = get_redis()

    async def insert_document(self, doc_id: str, text: str, filename: str = ""):
        if self._redis is None:
            raise RuntimeError("RAG service not initialized.")

        chunks = _chunk_text(text)
        if not chunks:
            return

        key_prefix = f"{RAG_PREFIX}doc:{doc_id}"
        pipe = self._redis.pipeline()
        pipe.sadd(RAG_DOC_IDS_KEY, doc_id.encode("utf-8"))
        pipe.hset(
            f"{key_prefix}:meta",
            mapping={
                b"filename": filename.encode("utf-8"),
                b"chunk_count": str(len(chunks)).encode("utf-8"),
            },
        )
        pipe.delete(f"{key_prefix}:chunks")
        for chunk in chunks:
            pipe.rpush(f"{key_prefix}:chunks", chunk.encode("utf-8"))
        pipe.execute()

    async def insert_text(self, text: str):
        """
        Backward-compatible method signature used by older call sites.
        Stores text under an ephemeral doc id.
        """
        import uuid

        await self.insert_document(str(uuid.uuid4()), text, filename="unknown")

    async def query(self, question: str, mode: str = "hybrid") -> str:
        _ = mode
        if self._redis is None:
            raise RuntimeError("RAG service not initialized.")

        q_tokens = _tokenize(question)
        if not q_tokens:
            return "[No relevant context found]"

        best_matches: list[tuple[int, str]] = []
        for raw_doc_id in self._redis.smembers(RAG_DOC_IDS_KEY):
            doc_id = raw_doc_id.decode("utf-8") if isinstance(raw_doc_id, bytes) else str(raw_doc_id)
            chunks = self._redis.lrange(f"{RAG_PREFIX}doc:{doc_id}:chunks", 0, -1)
            for raw_chunk in chunks:
                chunk = raw_chunk.decode("utf-8") if isinstance(raw_chunk, bytes) else str(raw_chunk)
                score = len(q_tokens.intersection(_tokenize(chunk)))
                if score > 0:
                    best_matches.append((score, chunk))

        if not best_matches:
            return "[No relevant context found]"

        best_matches.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [c for _, c in best_matches[:4]]
        return "\n\n".join(top_chunks)

    async def finalize(self):
        # Managed by app lifecycle; nothing to close per request.
        return None


# Compatibility alias used by app.agent.nodes
LiteRAGService = FalkorGraphRAGService


def ingest_document(doc_id: str, raw_bytes: bytes, filename: str) -> None:
    """
    Decode raw file bytes to text and insert into Falkor-backed RAG.
    Called by app/services/worker_threads.py in a background thread.
    Updates document status in FalkorDB: pending -> processing -> done/failed.

    Uses a fresh event loop per call to avoid conflicts with Flask's event loop
    or any existing loop running in the worker thread.
    """
    async def _run():
        _mark_status(doc_id, "processing")

        rag_service = LiteRAGService()
        await rag_service.initialize()

        try:
            if filename.lower().endswith(".pdf"):
                text = _extract_pdf_text(raw_bytes)
            else:
                text = raw_bytes.decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"[ingest] decode failed for {filename}: {e}")
            await rag_service.finalize()
            _mark_status(doc_id, "failed")
            return

        try:
            await rag_service.insert_document(doc_id=doc_id, text=text, filename=filename)
            logger.info(f"[ingest] {filename} ({doc_id}) indexed successfully")
            _mark_status(doc_id, "done")
        except Exception as e:
            logger.error(f"[ingest] insert failed for {filename}: {e}")
            _mark_status(doc_id, "failed")
        finally:
            await rag_service.finalize()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run())
    except Exception as e:
        logger.error(f"[ingest] Unhandled error for {doc_id}: {e}")
        _mark_status(doc_id, "failed")
    finally:
        loop.close()


def _extract_pdf_text(raw_bytes: bytes) -> str:
    """Extract plain text from PDF bytes using pypdf."""
    try:
        import io
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        logger.warning("pypdf not installed — treating PDF as raw bytes")
        return raw_bytes.decode("utf-8", errors="ignore")


def _mark_status(doc_id: str, status: str) -> None:
    """Update document status in FalkorDB (Redis)."""
    try:
        from app.database.document_store import set_document_status

        status_map = {
            "processing": "processing",
            "done": "done",
            "failed": "failed",
            "ready": "done",
            "error": "failed",
        }
        norm = status_map.get(status, "failed")

        if set_document_status(doc_id, norm):
            logger.info(f"[ingest] doc {doc_id} status -> {status}")
        else:
            logger.warning(
                f"[ingest] doc {doc_id} not found in store when marking {status}"
            )
    except Exception as e:
        logger.error(f"[ingest] failed to update status for {doc_id}: {e}")
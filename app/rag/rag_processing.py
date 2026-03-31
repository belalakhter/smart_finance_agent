import asyncio
import logging
import re
import os
import io
import uuid
import tempfile
from datetime import datetime
from typing import Optional, List, Tuple
from mistralai.client import Mistral

logger = logging.getLogger(__name__)

RAG_PREFIX = "smart_agent:rag:"

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


def _extract_pdf_text_mistral(raw_bytes: bytes) -> str:
    """Extract text from PDF using Mistral OCR API."""
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        logger.warning("MISTRAL_API_KEY not set - falling back to pypdf")
        return _extract_pdf_text_pypdf(raw_bytes)

    try:
        from mistralai.client import Mistral
        client = Mistral(api_key=api_key)
        
        uploaded = client.files.upload(
            file={
                "file_name": f"doc_{uuid.uuid4().hex[:8]}.pdf",
                "content": raw_bytes,
            },
            purpose="ocr"
        )
        file_id = uploaded.id
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={"type": "file", "file_id": file_id}
        )
        
        full_text = ""
        for page in ocr_response.pages:
            full_text += (page.markdown or "") + "\n\n"
            
        try:
            client.files.delete(file_id=file_id)
        except:
            pass

        return full_text
    except Exception as e:
        logger.error(f"Mistral OCR failed: {e}", exc_info=True)
        return _extract_pdf_text_pypdf(raw_bytes)


def _extract_pdf_text_pypdf(raw_bytes: bytes) -> str:
    """Extract plain text from PDF bytes using pypdf (Fallback)."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        logger.error(f"pypdf extraction failed: {e}")
        return raw_bytes.decode("utf-8", errors="ignore")


class GraphitiRAGService:
    """Graph-based RAG using Graphiti and FalkorDB."""

    def __init__(self):
        self.graphiti = None

    async def _ensure_initialized(self):
        if self.graphiti is None:
            from graphiti_core import Graphiti
            from graphiti_core.driver.falkordb_driver import FalkorDriver
            from app.llm.llm_client import get_graphiti_llm_client, get_graphiti_embedder

            host = os.environ.get("FALKORDB_HOST", "falkordb")
            port = int(os.environ.get("FALKORDB_PORT", "6379"))
            
            driver = FalkorDriver(host=host, port=port)
            self.graphiti = Graphiti(
                graph_driver=driver,
                llm_client=get_graphiti_llm_client(),
                embedder=get_graphiti_embedder()
            )

    async def initialize(self):
        await self._ensure_initialized()

    async def insert_document(self, doc_id: str, text: str, filename: str = ""):
        await self._ensure_initialized()
        if self.graphiti:
            await self.graphiti.add_episode(
                name=filename or doc_id,
                episode_body=text,
                source_description="Financial Document",
                reference_time=datetime.now(),
                group_id=doc_id
            )

    async def query(self, question: str, mode: str = "graph") -> str:
        await self._ensure_initialized()
        if self.graphiti:
            limit = 5 if mode == "graph" else 10
            search_results = await self.graphiti.search(query=question, num_results=limit)
            
            if not search_results:
                return "[No relevant context found]"
                
            parts = [f"- {res}" for res in search_results]
            return "\n".join(parts)
        return "[Graphiti not initialized]"

    async def finalize(self):
        pass


HybridRAGService = GraphitiRAGService

def ingest_document(doc_id: str, raw_bytes: bytes, filename: str) -> None:
    """
    Decode raw file bytes to text and insert into Graphiti-backed RAG (FalkorDB).
    Now with chunking for better granularity.
    """
    async def _run():
        logger.info(f"[ingest] Starting ingestion for {filename} ({doc_id})")
        _mark_status(doc_id, "processing")
        rag_service = GraphitiRAGService()
        await rag_service.initialize()
        
        try:
            if filename.lower().endswith(".pdf"):
                logger.info(f"[ingest] Extracting PDF text for {filename}...")
                text = _extract_pdf_text_mistral(raw_bytes)
            else:
                text = raw_bytes.decode("utf-8", errors="ignore")
            
            chunks = _chunk_text(text, chunk_size=5000, overlap=1200)
            logger.info(f"[ingest] Ingesting {len(chunks)} chunks for {filename}...")
            
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                
                logger.info(f"[ingest]   -> Processing chunk {i+1}/{len(chunks)}...")
                try:
                    await rag_service.insert_document(
                        doc_id=f"{doc_id}_{i}", 
                        text=chunk, 
                        filename=f"{filename} (part {i+1})"
                    )
                except Exception as chunk_e:
                    logger.warning(f"[ingest]   !! Chunk {i+1} failed but continuing: {chunk_e}")
            
            logger.info(f"[ingest] Successfully ingested {filename} ({len(chunks)} chunks).")
            _mark_status(doc_id, "completed")
        except Exception as e:
            logger.error(f"[ingest] failed for {filename}: {e}", exc_info=True)
            _mark_status(doc_id, "failed")
        finally:
            await rag_service.finalize()

    try:
        asyncio.run(_run())
    except Exception as outer_e:
        logger.error(f"[ingest] Global failure for {filename}: {outer_e}")


def _mark_status(doc_id: str, status: str) -> None:
    """Update document status in FalkorDB (Redis)."""
    try:
        from app.database.document_store import set_document_status
        status_map = {
            "processing": "processing",
            "done": "completed",
            "completed": "completed",
            "failed": "failed",
            "ready": "completed",
            "error": "failed",
        }
        norm = status_map.get(status, "failed")
        if set_document_status(doc_id, norm):
            logger.info(f"[ingest] doc {doc_id} status -> {status}")
    except Exception as e:
        logger.error(f"[ingest] failed to update status for {doc_id}: {e}")
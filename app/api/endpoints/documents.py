from flask import Blueprint, request, jsonify, send_file
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.database.connection import get_session
from app.database.models import Document, StatusEnum
import uuid
import io

documents_bp = Blueprint("documents", __name__)

def _session():
    return get_session()

@documents_bp.route("/documents", methods=["POST"])
def upload_document():
    """
    Upload a document for RAG ingestion
    ---
    tags:
      - Documents
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: PDF, TXT, or MD file to upload
    responses:
      201:
        description: Document uploaded and queued for ingestion
        schema:
          type: object
          properties:
            id:
              type: string
              example: "550e8400-e29b-41d4-a716-446655440000"
            filename:
              type: string
              example: "report.pdf"
            status:
              type: string
              example: "pending"
      400:
        description: Missing file or unsupported file type
      500:
        description: Database error
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "No file selected"}), 400

    allowed = {"pdf", "txt", "md"}
    ext = f.filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed:
        return jsonify({"error": f"File type '.{ext}' not allowed. Use: {allowed}"}), 400

    raw = f.read()
    filename = f.filename

    doc = Document(
        id=uuid.uuid4(),
        filename=filename,
        content=raw,
        status=StatusEnum.pending,
    )

    with _session() as session:
        try:
            session.add(doc)
            session.commit()
            session.refresh(doc)
            doc_id     = str(doc.id)
            doc_name   = doc.filename
            doc_status = doc.status.value
        except SQLAlchemyError as e:
            session.rollback()
            return jsonify({"error": str(e)}), 500

    try:
        from app.services.worker_threads import submit_task 
        from app.rag.lite_rag import ingest_document
        submit_task(ingest_document, doc_id, raw, filename)
    except Exception:
        pass

    return jsonify({
        "id":       doc_id,
        "filename": doc_name,
        "status":   doc_status,
    }), 201


@documents_bp.route("/documents", methods=["GET"])
def list_documents():
    """
    List all uploaded documents
    ---
    tags:
      - Documents
    responses:
      200:
        description: List of all documents
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
                example: "550e8400-e29b-41d4-a716-446655440000"
              filename:
                type: string
                example: "report.pdf"
              status:
                type: string
                enum: [pending, processing, done, failed]
                example: "done"
    """
    with _session() as session:
        docs = session.query(Document).all()
        return jsonify([
            {
                "id": str(d.id),
                "filename": d.filename,
                "status": d.status.value,
            }
            for d in docs
        ]), 200


@documents_bp.route("/documents/<doc_id>", methods=["GET"])
def get_document(doc_id):
    """
    Download a document by ID
    ---
    tags:
      - Documents
    parameters:
      - in: path
        name: doc_id
        required: true
        type: string
        description: UUID of the document
    produces:
      - application/octet-stream
    responses:
      200:
        description: File download
      404:
        description: Document not found
    """
    with _session() as session:
        doc = session.query(Document).filter_by(id=doc_id).first()
        if not doc:
            return jsonify({"error": "Document not found"}), 404
        return send_file(
            io.BytesIO(doc.content),
            download_name=doc.filename,
            as_attachment=True,
        )


@documents_bp.route("/documents/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    """
    Delete a document by ID
    ---
    tags:
      - Documents
    parameters:
      - in: path
        name: doc_id
        required: true
        type: string
        description: UUID of the document to delete
    responses:
      200:
        description: Document deleted successfully
        schema:
          type: object
          properties:
            deleted:
              type: string
              example: "550e8400-e29b-41d4-a716-446655440000"
      404:
        description: Document not found
      500:
        description: Database error
    """
    with _session() as session:
        doc = session.query(Document).filter_by(id=doc_id).first()
        if not doc:
            return jsonify({"error": "Document not found"}), 404
        try:
            session.delete(doc)
            session.commit()
            return jsonify({"deleted": doc_id}), 200
        except SQLAlchemyError as e:
            session.rollback()
            return jsonify({"error": str(e)}), 500
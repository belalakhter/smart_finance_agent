from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.database.connection import get_session
from app.database.models import Chat
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
import uuid

chat_bp = Blueprint("chat", __name__)

def _session():
    return get_session()

@chat_bp.route("/chats", methods=["POST"])
def create_chat():
    """
    Create a new chat
    ---
    tags:
      - Chats
    parameters:
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            name:
              type: string
              example: My conversation
    responses:
      201:
        description: Chat created successfully
        schema:
          type: object
          properties:
            id:
              type: string
              example: "550e8400-e29b-41d4-a716-446655440000"
            name:
              type: string
              example: My conversation
            messages:
              type: array
              items: {}
      500:
        description: Database error
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name", "New Conversation")

    chat = Chat(id=uuid.uuid4(), name=name, messages=[])

    with _session() as session:
        try:
            session.add(chat)
            session.commit()
            session.refresh(chat)
            return jsonify({"id": str(chat.id), "name": chat.name, "messages": chat.messages}), 201
        except SQLAlchemyError as e:
            session.rollback()
            return jsonify({"error": str(e)}), 500


@chat_bp.route("/chats", methods=["GET"])
def list_chats():
    """
    List all chats
    ---
    tags:
      - Chats
    responses:
      200:
        description: List of all chats
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
                example: "550e8400-e29b-41d4-a716-446655440000"
              name:
                type: string
                example: My conversation
              message_count:
                type: integer
                example: 5
              preview:
                type: string
                example: "Hello, how can I help you…"
    """
    with _session() as session:
        chats = session.query(Chat).all()
        return jsonify([
            {
                "id": str(c.id),
                "name": c.name,
                "message_count": len(c.messages) if c.messages else 0,
                "preview": _preview(c.messages),
            }
            for c in chats
        ]), 200


@chat_bp.route("/chats/<chat_id>", methods=["GET"])
def get_chat(chat_id):
    """
    Get a chat by ID
    ---
    tags:
      - Chats
    parameters:
      - in: path
        name: chat_id
        required: true
        type: string
        description: UUID of the chat
    responses:
      200:
        description: Chat object with full message history
        schema:
          type: object
          properties:
            id:
              type: string
            name:
              type: string
            messages:
              type: array
              items:
                type: object
                properties:
                  role:
                    type: string
                    example: user
                  content:
                    type: string
                    example: Hello!
      404:
        description: Chat not found
    """
    with _session() as session:
        chat = session.query(Chat).filter_by(id=chat_id).first()
        if not chat:
            return jsonify({"error": "Chat not found"}), 404
        return jsonify({"id": str(chat.id), "name": chat.name, "messages": chat.messages}), 200


@chat_bp.route("/chats/<chat_id>/messages", methods=["POST"])
def send_message(chat_id):
    """
    Send a message to a chat
    ---
    tags:
      - Chats
    parameters:
      - in: path
        name: chat_id
        required: true
        type: string
        description: UUID of the chat
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - message
          properties:
            message:
              type: string
              example: "What is the weather today?"
    responses:
      200:
        description: Agent reply and updated message history
        schema:
          type: object
          properties:
            reply:
              type: string
              example: "I don't have access to real-time weather data."
            messages:
              type: array
              items:
                type: object
                properties:
                  role:
                    type: string
                    example: assistant
                  content:
                    type: string
      400:
        description: Missing message field
      404:
        description: Chat not found
      500:
        description: Database error
    """
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    with _session() as session:
        chat = session.query(Chat).filter_by(id=chat_id).first()
        if not chat:
            return jsonify({"error": "Chat not found"}), 404

        messages = list(chat.messages or [])
        messages.append({"role": "user", "content": message})

        try:
            from app.agent.graph import run_agent
            reply = run_agent(chat_id=str(chat.id), messages=messages)
        except Exception as e:
            reply = f"[Agent error] {e}"

        messages.append({"role": "assistant", "content": reply})
        chat.messages = messages
        flag_modified(chat, "messages")

        try:
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            return jsonify({"error": str(e)}), 500

        return jsonify({"reply": reply, "messages": messages}), 200


@chat_bp.route("/chats/<chat_id>", methods=["PATCH"])
def rename_chat(chat_id):
    """
    Rename a chat
    ---
    tags:
      - Chats
    parameters:
      - in: path
        name: chat_id
        required: true
        type: string
        description: UUID of the chat
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              example: "Renamed conversation"
    responses:
      200:
        description: Chat renamed successfully
        schema:
          type: object
          properties:
            id:
              type: string
            name:
              type: string
      400:
        description: Missing name field
      404:
        description: Chat not found
      500:
        description: Database error
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    with _session() as session:
        chat = session.query(Chat).filter_by(id=chat_id).first()
        if not chat:
            return jsonify({"error": "Chat not found"}), 404
        chat.name = name
        try:
            session.commit()
            return jsonify({"id": str(chat.id), "name": chat.name}), 200
        except SQLAlchemyError as e:
            session.rollback()
            return jsonify({"error": str(e)}), 500


@chat_bp.route("/chats/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    """
    Delete a chat
    ---
    tags:
      - Chats
    parameters:
      - in: path
        name: chat_id
        required: true
        type: string
        description: UUID of the chat to delete
    responses:
      200:
        description: Chat deleted successfully
        schema:
          type: object
          properties:
            deleted:
              type: string
              example: "550e8400-e29b-41d4-a716-446655440000"
      404:
        description: Chat not found
      500:
        description: Database error
    """
    with _session() as session:
        chat = session.query(Chat).filter_by(id=chat_id).first()
        if not chat:
            return jsonify({"error": "Chat not found"}), 404
        try:
            session.delete(chat)
            session.commit()
            return jsonify({"deleted": chat_id}), 200
        except SQLAlchemyError as e:
            session.rollback()
            return jsonify({"error": str(e)}), 500


def _preview(messages):
    if not messages:
        return "No messages yet"
    user_msgs = [m for m in messages if m.get("role") == "user"]
    if not user_msgs:
        return "No messages yet"
    raw = user_msgs[-1].get("content", "")
    return raw[:40] + ("…" if len(raw) > 40 else "")
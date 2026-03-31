import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.database.connection import get_redis

logger = logging.getLogger(__name__)

class ChatKVStore:
    """
    Redis-backed store for chat messages.
    """

    def _key(self, key: str) -> str:
        return f"smart_agent:chat:{key}:messages"

    def push(self, key: str, message: dict) -> None:
        """
        Append a message to a chat list in Redis.
        """
        try:
            r = get_redis()
            enriched_message = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                **message
            }
            r.rpush(self._key(key), json.dumps(enriched_message))
        except Exception as e:
            logger.error(f"[ChatKVStore] push failed: {e}")

    def get(self, key: str) -> List[dict]:
        """
        Get all messages for a key from Redis.
        """
        try:
            r = get_redis()
            raw_msgs = r.lrange(self._key(key), 0, -1)
            return [json.loads(m) for m in raw_msgs]
        except Exception as e:
            logger.error(f"[ChatKVStore] get failed: {e}")
            return []

    def delete(self, key: str) -> None:
        """
        Delete a chat history from Redis.
        """
        try:
            r = get_redis()
            r.delete(self._key(key))
        except Exception as e:
            logger.error(f"[ChatKVStore] delete failed: {e}")

    def size(self, key: str) -> int:
        """
        Number of messages in a chat from Redis.
        """
        try:
            r = get_redis()
            return r.llen(self._key(key))
        except Exception as e:
            logger.error(f"[ChatKVStore] size failed: {e}")
            return 0

    def clear(self) -> None:
        """
        Clear all chat histories (DANGER: only for testing).
        """
        try:
            r = get_redis()
            keys = r.keys("smart_agent:chat:*:messages")
            if keys:
                r.delete(*keys)
        except Exception as e:
            logger.error(f"[ChatKVStore] clear failed: {e}")

chat_store = ChatKVStore()
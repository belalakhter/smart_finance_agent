import threading
from typing import Dict, List, Any, Optional
from datetime import datetime
import copy


class ChatKVStore:
    """
    In-memory KV store for chat messages.
    """

    def __init__(self):
        self._store: Dict[str, List[dict]] = {}
        self._lock = threading.RLock()


    def push(self, key: str, message: dict) -> None:
        """
        Append a message to a chat list.
        """
        with self._lock:
            if key not in self._store:
                self._store[key] = []

            enriched_message = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                **message
            }

            self._store[key].append(enriched_message)

    def get(self, key: str) -> List[dict]:
        """
        Get all messages for a key.
        """
        with self._lock:
            return copy.deepcopy(self._store.get(key, []))

    def pop(self, key: str) -> Optional[List[dict]]:
        """
        Remove and return entire message list.
        """
        with self._lock:
            return self._store.pop(key, None)

    def delete(self, key: str) -> None:
        """
        Delete a chat history.
        """
        with self._lock:
            self._store.pop(key, None)

    def exists(self, key: str) -> bool:
        """
        Check if key exists.
        """
        with self._lock:
            return key in self._store

    def trim(self, key: str, max_length: int = 50) -> None:
        """
        Keep only last N messages (like Redis list trim).
        """
        with self._lock:
            if key in self._store:
                self._store[key] = self._store[key][-max_length:]

    def last(self, key: str) -> Optional[dict]:
        """
        Get last message.
        """
        with self._lock:
            if key in self._store and self._store[key]:
                return self._store[key][-1]
            return None

    def size(self, key: str) -> int:
        """
        Number of messages in a chat.
        """
        with self._lock:
            return len(self._store.get(key, []))

    def clear(self) -> None:
        """
        Clear entire store.
        """
        with self._lock:
            self._store.clear()


chat_store = ChatKVStore()
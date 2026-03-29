import os
from typing import Optional

from redis import Redis
from redis.connection import ConnectionPool

_pool: Optional[ConnectionPool] = None
_client: Optional[Redis] = None


def init_connection_pool(
    minconn: int = 1,
    maxconn: int = 5,
    force: bool = False,
) -> ConnectionPool:
    """
    Initialize a Redis connection pool targeting FalkorDB (Redis-compatible).

    Use env: FALKORDB_HOST / FALKORDB_PORT (defaults match docker-compose: falkordb:6379).
    ``minconn`` is accepted for compatibility with existing callers but is not used by redis-py.
    """
    global _pool, _client

    if force and _pool is not None:
        _pool.disconnect()
        _pool = None
        _client = None

    if _pool is None:
        host = os.environ.get(
            "FALKORDB_HOST",
            os.environ.get("REDIS_HOST", "falkordb"),
        )
        port = int(
            os.environ.get(
                "FALKORDB_PORT",
                os.environ.get("REDIS_PORT", "6379"),
            )
        )
        db = int(os.environ.get("REDIS_DB", "0"))

        _pool = ConnectionPool(
            host=host,
            port=port,
            db=db,
            max_connections=maxconn,
            decode_responses=False,
        )
        _client = Redis(connection_pool=_pool)
        print(f"FalkorDB (Redis) connection pool initialized ({host}:{port}).")

    return _pool


def get_redis() -> Redis:
    if _client is None:
        raise RuntimeError("Redis not initialized. Call init_connection_pool() first.")
    return _client


def close_connection_pool() -> None:
    global _pool, _client
    if _pool is not None:
        _pool.disconnect()
        _pool = None
        _client = None
        print("FalkorDB (Redis) connection pool closed.")

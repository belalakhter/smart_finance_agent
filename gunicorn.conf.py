import logging

logger = logging.getLogger(__name__)


def post_fork(server, worker):
    """
    Called in the worker process after forking from master.
    """
    from app.database.connection import init_connection_pool
    from app.services.worker_threads import init_worker

    logger.info(f"[worker {worker.pid}] Reinitializing DB connection pool after fork...")
    init_connection_pool(minconn=1, maxconn=5)

    logger.info(f"[worker {worker.pid}] Reinitializing async worker after fork...")
    init_worker(max_workers=10)


def worker_exit(server, worker):
    """
    Called just before a worker exits (SIGTERM or graceful shutdown).
    """
    from app.services.worker_threads import shutdown_worker

    logger.info(f"[worker {worker.pid}] Shutting down async worker...")
    shutdown_worker()
import os
from flask import Flask, jsonify, send_from_directory
from database.connection import init_connection_pool
from services.worker_threads import init_worker, shutdown_worker
from services.logger import get_logger
from api.routes import register_routes

logger = get_logger(__name__, level="INFO")

UI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ui")


def create_flask_app():
    app = Flask(__name__, static_folder=None)

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "healthy", "server_active": True})

    @app.route("/", methods=["GET"])
    def serve_index():
        return send_from_directory(UI_DIR, "index.html")

    @app.route("/<path:filename>", methods=["GET"])
    def serve_static(filename):
        filepath = os.path.join(UI_DIR, filename)
        if os.path.isfile(filepath):
            return send_from_directory(UI_DIR, filename)
        return jsonify({"error": "not found"}), 404

    register_routes(app)
    return app


if __name__ == "__main__":
    logger.info("Initializing async worker...")
    init_worker(max_workers=10)

    init_connection_pool(minconn=1, maxconn=5)
    logger.info("Database initialized...")

    app = create_flask_app()
    port = int(os.getenv("PORT", 3000))
    logger.info(f"Starting Flask server on port {port}...")

    try:
        app.run(host="0.0.0.0", port=port)
    finally:
        logger.info("Shutting down worker...")
        shutdown_worker()
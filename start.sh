#!/usr/bin/env bash

cleanup() {
  echo ""
  echo "Stopping containers, cleaning up volumes, and removing app image..."
  docker compose down -v
  docker rmi -f smart_chat_agent-app:latest 2>/dev/null || true
  exit 0
}

trap cleanup SIGINT SIGTERM

set -e

echo "Performing initial cleanup..."
docker compose down -v 2>/dev/null || true
docker rmi -f smart_chat_agent-app:latest 2>/dev/null || true

echo "Building and starting services..."
docker compose up -d --build

echo "Application Start! "
echo "Following logs from the app container (Ctrl+C to stop and cleanup)..."

docker compose logs -f app
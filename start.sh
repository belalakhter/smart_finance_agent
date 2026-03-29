#!/usr/bin/env bash

set -euo pipefail

cleanup_done=0

cleanup() {
  if [[ "$cleanup_done" -eq 1 ]]; then
    return 0
  fi
  cleanup_done=1
  trap - SIGINT SIGTERM

  echo ""
  echo "Stopping containers, cleaning up volumes, and removing local images..."
  docker compose down -v --remove-orphans --rmi local || true

  # Fallback for older compose behavior or renamed projects.
  docker rmi -f smart_finance_agent-app:latest 2>/dev/null || true
  docker rmi -f smart_chat_agent-app:latest 2>/dev/null || true
  exit 0
}

trap cleanup SIGINT SIGTERM

echo "Performing initial cleanup..."
docker compose down -v --remove-orphans --rmi local 2>/dev/null || true
docker rmi -f smart_finance_agent-app:latest 2>/dev/null || true
docker rmi -f smart_chat_agent-app:latest 2>/dev/null || true

echo "Building and starting services..."
docker compose up -d --build

echo "Application Start! "
echo "Following logs from the app container (Ctrl+C to stop and cleanup)..."

docker compose logs -f app
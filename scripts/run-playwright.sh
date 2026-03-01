#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "==> Building frontend"
cd "$FRONTEND_DIR"
npm run build >/dev/null

echo "==> Seeding database"
cd "$ROOT_DIR"
poetry run python scripts/init_db.py >/tmp/playwright-seed.log 2>&1 || true

echo "==> Starting backend server"
cd "$ROOT_DIR"
PYTHONPATH="$ROOT_DIR" uvicorn buro.main:app --host 127.0.0.1 --port 8000 >/tmp/playwright-backend.log 2>&1 &
API_PID=$!

cleanup() {
  echo "==> Shutting down backend"
  kill $API_PID >/dev/null 2>&1 || true
}

trap cleanup EXIT

cd "$FRONTEND_DIR"
echo "==> Running Playwright tests"
npm run test:e2e

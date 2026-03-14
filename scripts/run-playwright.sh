#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "==> Building frontend"
cd "$FRONTEND_DIR"
npm run build:fast >/dev/null

echo "==> Seeding database"
cd "$ROOT_DIR"
poetry run python scripts/init_db.py >/tmp/playwright-seed.log 2>&1 || true

echo "==> Starting backend server"
cd "$ROOT_DIR"
if lsof -ti tcp:8000 >/dev/null 2>&1; then
  echo "==> Port 8000 in use, stopping existing process"
  lsof -ti tcp:8000 | xargs -r kill >/dev/null 2>&1 || true
  sleep 1
fi
FRONTEND_BUILD_PATH="$FRONTEND_DIR/build" \
PYTHONPATH="$ROOT_DIR" \
poetry run uvicorn buro.main:app --host 127.0.0.1 --port 8000 >/tmp/playwright-backend.log 2>&1 &
API_PID=$!

echo "==> Waiting for backend to be ready"
for i in {1..30}; do
  if curl -fs http://127.0.0.1:8000/docs >/dev/null; then
    break
  fi
  if ! kill -0 "$API_PID" >/dev/null 2>&1; then
    echo "Backend exited early. Log output:"
    sed -n '1,120p' /tmp/playwright-backend.log
    exit 1
  fi
  sleep 1
done

if ! curl -fs http://127.0.0.1:8000/docs >/dev/null; then
  echo "Backend did not become ready in time. Log output:"
  sed -n '1,120p' /tmp/playwright-backend.log
  exit 1
fi

cleanup() {
  echo "==> Shutting down backend"
  kill $API_PID >/dev/null 2>&1 || true
}

trap cleanup EXIT

cd "$FRONTEND_DIR"
echo "==> Running Playwright tests"
npm run test:e2e

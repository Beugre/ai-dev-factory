#!/usr/bin/env bash
# Déploiement sur le VPS — lancé par GitHub Actions ou manuellement.
# Usage depuis le VPS : cd /opt/ai-dev-factory && bash infra/scripts/deploy.sh
set -euo pipefail

APP_DIR="/opt/ai-dev-factory"
cd "$APP_DIR"

echo "=== Pull dernière version ==="
git pull origin main

echo "=== Build et démarrage ==="
docker compose -f docker-compose.prod.yml pull --quiet
docker compose -f docker-compose.prod.yml up -d --build --remove-orphans

echo "=== Migrations ==="
docker compose -f docker-compose.prod.yml exec -T api alembic upgrade head

echo "=== Healthcheck ==="
for i in $(seq 1 30); do
  if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ API répond"
    break
  fi
  sleep 2
done

echo "✅ Déploiement terminé"

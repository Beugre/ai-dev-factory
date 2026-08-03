# Runbook — Développement local

## Prérequis
- Python 3.12, Node 22, Docker.

## Option A — Docker Compose (recommandé)
```bash
cp .env.example .env
docker compose up --build
```
- API : http://localhost:8000/docs
- Web : http://localhost:5173
- Les migrations Alembic sont appliquées au démarrage de l'API.

## Option B — Local
```bash
make install                 # venv Python + npm install
# Terminal 1 : API (SQLite par défaut, aucun service requis)
. .venv/bin/activate && (cd packages/adf && uvicorn adf.api.app:app --reload)
# Terminal 2 : Web
cd apps/web && npm run dev
```

## Démo hors-ligne
```bash
make demo
```

## Tests & qualité
```bash
make lint        # ruff + eslint
make typecheck   # mypy + tsc
make test        # pytest + vitest
```

## Base de données
- Local par défaut : SQLite (`sqlite+aiosqlite:///./adf.db`), tables créées
  automatiquement.
- Postgres : définir `DATABASE_URL=postgresql+asyncpg://…` puis `make migrate`.

## Dépannage
- `ModuleNotFoundError: adf` → `pip install -e ./packages/adf` dans le venv actif.
- Port occupé → ajuster les ports dans `docker-compose.yml`.

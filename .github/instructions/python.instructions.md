---
applyTo: "packages/adf/**/*.py"
---

# Instructions Python

- Python 3.12. Toujours `from __future__ import annotations`.
- Typage strict (mypy). Pas de `Any` injustifié.
- Pydantic v2 pour la validation ; valider toute sortie IA avant persistance.
- SQLAlchemy 2 en mode asynchrone. Accès DB uniquement via `SqlAlchemyUnitOfWork`.
- Respecter l'architecture hexagonale : le domaine (`adf/domain`) ne dépend
  d'aucun framework externe.
- Les transitions d'état passent **obligatoirement** par `domain/state_machine`.
- Journalisation via `adf.infrastructure.logging.get_logger` (JSON, sans secret).
- Exceptions métier : sous-classes de `DomainError`, mappées par l'API.
- Ne jamais avaler une exception silencieusement.
- Tests : `pytest` + `pytest-asyncio`, adapters mock, base SQLite isolée.
- Lint : `ruff check`. Format des lignes ≤ 100 caractères.

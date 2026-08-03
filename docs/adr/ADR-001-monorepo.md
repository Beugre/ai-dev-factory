# ADR-001 — Monorepo et organisation des packages

## Statut
Accepté.

## Contexte
La spécification demande un monorepo avec `apps/{api,worker,discord-bot,web}` et
`packages/{domain,application,github-adapter,agent-runtime,notification-gateway,
shared}`. Il faut un projet réellement exécutable et testable en une session.

## Décision
- Monorepo unique.
- Le backend est **un seul package Python installable** `adf`
  (`packages/adf`), organisé en sous-modules qui **mappent** l'architecture
  hexagonale et les packages demandés :
  - `packages/domain` → `adf.domain`
  - `packages/application` → `adf.application`
  - `packages/github-adapter` → `adf.adapters.github`
  - `packages/agent-runtime` → `adf.agent_runtime` + `adf.adapters.agent_runtime`
  - `packages/notification-gateway` → `adf.adapters.notification`
  - `packages/shared` → `adf.config`, `adf.infrastructure`
- Les apps `api`, `worker`, `discord-bot` sont des **entrypoints** de `adf`
  (`adf.api.app`, `adf.worker.main`, `adf.discord_bot.main`). `apps/web` est la
  PWA.

## Justification
Six distributions Python séparées multiplieraient les `pyproject`, les
dépendances croisées et le risque d'échec d'installation, sans bénéfice pour la
V1. Un package unique bien découpé garantit l'isolation des couches (vérifiée
par les imports et mypy) tout en restant installable et testable simplement.

## Conséquences
- `import adf.domain` reste pur (aucune dépendance externe).
- Extraction future en packages séparés possible sans réécriture (les frontières
  sont déjà des modules/ports).
- Différence assumée avec l'arborescence littérale de la spec, documentée ici.

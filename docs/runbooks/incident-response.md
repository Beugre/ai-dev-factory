# Runbook — Réponse à incident

## Détection
- Endpoint `/health` (liveness) et `/ready` (DB joignable).
- Métriques Prometheus sur `/metrics` (protégé par `METRICS_TOKEN` si défini).
- Erreurs récentes visibles dans l'UI (Agent Runs) et via `GET /agent-runs`.
- Logs JSON structurés avec `correlation_id`.

## Triage
1. Identifier le `correlation_id` de la requête/action fautive.
2. Corréler dans `AuditLog` (`GET /audit-logs?entity_type=…&entity_id=…`).
3. Vérifier les `AgentRun` en échec (`state=failed`, champ `error`).

## Incidents fréquents
| Symptôme | Cause probable | Action |
|----------|----------------|--------|
| `/ready` = not-ready | DB indisponible | Vérifier Postgres / `DATABASE_URL` |
| Webhooks ignorés | Signature invalide | Vérifier `GITHUB_WEBHOOK_SECRET` |
| Dispatch non confirmé | Droits/API Copilot | Repli `manual`, vérifier le token |
| Staging bloqué | CI rouge | Corriger la CI (jamais contourner) |
| Fuite de secret suspectée | Token exposé | Révoquer + rotation (voir secrets.md) |

## Rollback
- Migration : `alembic downgrade -1` (jamais destructif sans validation humaine).
- Déploiement : redéployer la version précédente via `DeploymentGateway`.

## Post-mortem
Consigner cause racine, impact, correctif et action de prévention. Créer une
issue « technical task » et, si structurant, une ADR.

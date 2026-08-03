# Runbook — Staging & previews

Le staging peut être **automatisé**. La production nécessite **toujours** une
validation humaine explicite.

## Modes de déploiement
`DEPLOYMENT_MODE = mock | local | webhook`

| Mode | Usage | Variables |
|------|-------|-----------|
| `mock` | Démo/tests, aucune infra | `STAGING_BASE_URL` |
| `local` | Preview locale via la stack Compose | `STAGING_BASE_URL` |
| `webhook` | Déclenche un déploiement externe | `STAGING_DEPLOY_WEBHOOK_URL` |

La V1 n'impose ni Vercel, ni Render, ni Kubernetes.

## Flux staging
1. La PR a une CI **verte** (sinon `approve_staging` lève `CIFailure`).
2. Le propriétaire valide le staging (Web/Discord ou
   `POST /pull-requests/{id}/approve-staging`).
3. `DeploymentGateway.deploy(...)` est appelé selon `DEPLOYMENT_MODE`.
4. Un `Deployment` est enregistré et l'URL de preview attachée à la PR.

## Déploiement staging via GitHub Actions
`.github/workflows/deploy-staging.yml` (manuel). Sans
`STAGING_DEPLOY_WEBHOOK_URL`, l'étape est simulée.

## Production
`.github/workflows/deploy-production.yml` est **désactivé par défaut**, protégé
par l'environnement GitHub `production` (required reviewers) et un garde-fou
`vars.PRODUCTION_ENABLED == 'true'`. Côté application,
`ApprovalService.ensure_production_approved` bloque tout déploiement sans
approbation humaine.

# Runbook — Configuration GitHub

## 1. Choisir la stratégie d'authentification
- **PAT fine-grained** (le plus simple) ou **GitHub App** (recommandé en équipe).
- Permissions minimales : voir `docs/security/secrets.md`.

## 2. Variables d'environnement
```
GITHUB_OWNER=mon-owner
GITHUB_TARGET_REPO=mon-repo
GITHUB_DEFAULT_BRANCH=main
GITHUB_USER_TOKEN=...            # active RealGitHubGateway
GITHUB_WEBHOOK_SECRET=...        # secret partagé du webhook
COPILOT_DISPATCH_MODE=issue_assignment
COPILOT_CUSTOM_AGENT=developer
COPILOT_MODEL=
```
Dès que `GITHUB_USER_TOKEN` est défini, le backend utilise le gateway réel.

## 3. Créer les labels
```bash
make bootstrap-github
```
Script idempotent : `infra/scripts/bootstrap_github_labels.py`.

## 4. Configurer le webhook
- URL : `https://<votre-domaine>/api/v1/webhooks/github`
- Content type : `application/json`
- Secret : `GITHUB_WEBHOOK_SECRET`
- Événements : issues, issue_comment, pull_request, pull_request_review,
  pull_request_review_comment, check_run, check_suite, workflow_run, deployment,
  deployment_status.

## 5. Dispatch Copilot
- `issue_assignment` : affecte `copilot-swe-agent[bot]` à l'issue.
- `agent_tasks_api` : API agentique GitHub (**préversion**, désactivée par
  défaut ; nécessite un compte/forfait éligible).
- `manual` : laisse l'issue prête à être affectée à la main.

Le succès n'est confirmé que si GitHub le confirme.

## 6. Protections de branche
- Exiger une revue humaine et une CI verte avant fusion sur `main`.
- Ne jamais autoriser l'auto-fusion par un agent.

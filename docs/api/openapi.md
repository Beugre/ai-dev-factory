# API

L'API REST est documentée via OpenAPI. Une fois l'API lancée :
- Swagger UI : http://localhost:8000/docs
- ReDoc : http://localhost:8000/redoc
- Spec brute : http://localhost:8000/openapi.json

Préfixe : `/api/v1`.

## Endpoints

```
POST   /projects
GET    /projects
GET    /projects/{id}

POST   /feature-requests
GET    /feature-requests
GET    /feature-requests/{id}
POST   /feature-requests/{id}/analyze
POST   /feature-requests/{id}/approve-scope
POST   /feature-requests/{id}/request-changes
POST   /feature-requests/{id}/cancel
GET    /feature-requests/{id}/questions

POST   /questions/{id}/answer

GET    /epics/{id}
GET    /epics/{id}/stories

GET    /stories
GET    /stories/{id}
POST   /stories/{id}/dispatch
POST   /stories/{id}/pause
POST   /stories/{id}/resume

GET    /approvals
POST   /approvals/{id}/approve
POST   /approvals/{id}/reject

GET    /pull-requests
GET    /pull-requests/{id}
POST   /pull-requests/{id}/request-changes
POST   /pull-requests/{id}/approve-staging

GET    /agent-runs
GET    /deployments
GET    /audit-logs

POST   /webhooks/github
GET    /health
GET    /ready
```

## Conventions
- Pagination : `?limit=&offset=` (réponse `{items,total,limit,offset}`).
- Filtres : query params (`project_id`, `state`, `status`, `priority`, …).
- Erreurs structurées : `{ "code", "message", "correlation_id" }`.
- Corrélation : en-tête `X-Correlation-ID` (généré si absent, renvoyé en réponse).
- Codes : 404 not found, 409 transition/état invalide, 403 approbation requise.

## Exemple

```bash
curl -X POST http://localhost:8000/api/v1/feature-requests \
  -H 'Content-Type: application/json' \
  -d '{"project_id":"<id>","title":"Reset password",
       "raw_request":"Je veux réinitialiser mon mot de passe"}'
```

La spec peut être exportée en CI (`.github/workflows/openapi.yml`).

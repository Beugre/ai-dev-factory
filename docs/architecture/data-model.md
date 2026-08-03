# Modèle de données

```mermaid
erDiagram
  Project ||--o{ FeatureRequest : contient
  FeatureRequest ||--o{ ClarificationQuestion : pose
  FeatureRequest ||--o{ Epic : génère
  Epic ||--o{ Story : découpe
  Story ||--o{ PullRequest : produit
  Project ||--o{ AgentRun : trace
  Project ||--o{ Approval : requiert
  Project ||--o{ Deployment : déploie
  PullRequest ||--o{ Deployment : déclenche

  Project {
    string id
    string slug
    string github_owner
    string github_repo
    string default_branch
    string status
  }
  FeatureRequest {
    string id
    string title
    string state
    string priority
    string source
  }
  Story {
    string id
    string status
    string assigned_agent
    int github_issue_number
    int pull_request_number
  }
  Approval {
    string id
    string approval_type
    string decision
  }
```

## Entités
Voir `packages/adf/adf/infrastructure/db/models.py`. Toutes les entités ont
`id` (UUID), `created_at`, `updated_at`. Les états sont des `StrEnum` explicites
(`packages/adf/adf/domain/enums.py`), persistés via `StrEnumType`.

Table clé pour l'idempotence : `webhook_events` (clé unique = delivery id).

## Contraintes & index
- `projects.slug` unique.
- `pull_requests(repository, number)` unique.
- Index sur les états (`feature_requests.state`, `stories.status`,
  `approvals.decision`) et sur `audit_logs(entity_type, entity_id)`.

## Multi-projets
La V1 gère un propriétaire et un dépôt cible configurables, mais le modèle
supporte déjà **plusieurs projets** (FK `project_id`).

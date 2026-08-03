# AI Dev Factory

Pilotez la construction d'une application **depuis votre téléphone**. Vous
décrivez un besoin en langage naturel ; des agents IA analysent, découpent en
epic/stories, génèrent les critères d'acceptation Gherkin, posent les questions
bloquantes, créent les issues GitHub, affectent le développement à GitHub
Copilot, suivent PR/CI/preview, font intervenir revue/QA/documentation, et vous
demandent de **valider** les actions sensibles depuis Discord ou l'interface web.

> **Principe fondamental** : l'IA exécute le travail, mais les actions sensibles
> (fusion sur `main`, production, migration destructive, suppression de données,
> etc.) exigent une **validation humaine explicite**. Le staging peut être
> automatisé.

## Démarrage rapide

```bash
cp .env.example .env
docker compose up --build
```

Puis :
- API : http://localhost:8000 (docs OpenAPI sur `/docs`)
- Web (PWA) : http://localhost:5173

### Démo sans aucun compte externe

```bash
make install          # venv Python 3.12 + npm install
make demo             # parcours complet en mode mock
```

`make demo` déroule : demande → analyse Product Owner → questions → réponses →
epic + stories → validation → issues (mock) → dispatch Copilot (mock) → PR
(mock) → CI verte → revue + QA → staging (mock) → demande de modification →
nouvelle itération → acceptation.

## Arborescence

```
ai-dev-factory/
├── apps/
│   └── web/                 # PWA React + TS + Vite + Tailwind
├── packages/
│   └── adf/                 # Backend Python (hexagonal)
│       ├── adf/domain/          # entités, enums, machine à états, contrats
│       ├── adf/application/     # services (use-cases) + orchestrateur démo
│       ├── adf/ports/           # interfaces (agent, github, notif, deploy)
│       ├── adf/adapters/        # implémentations mock + réelles
│       ├── adf/infrastructure/  # DB async, logging, métriques
│       ├── adf/api/             # FastAPI (routers fins)
│       ├── adf/worker/          # worker Redis
│       ├── adf/discord_bot/     # bot Discord (sécurité + routing)
│       └── adf/agent_runtime/   # prompts versionnés
├── infra/{docker,n8n,scripts}/
├── docs/                    # architecture, sécurité, runbooks, ADR
├── tests/                   # integration / contract / e2e (racine)
└── .github/                 # agents, instructions, workflows, templates
```

> Les apps `worker` et `discord-bot` partagent l'image backend et vivent comme
> sous-modules de `adf` (voir `docs/adr/ADR-001-monorepo.md`).

## Commandes (`make`)

| Cible | Effet |
|-------|-------|
| `make install` | venv + dépendances backend & frontend |
| `make up` / `make down` | Docker Compose |
| `make lint` / `make typecheck` / `make test` | qualité |
| `make demo` | workflow complet en mode mock |
| `make migrate` / `make migration msg="…"` | Alembic |
| `make seed` | projet de démonstration |
| `make bootstrap-github` | labels GitHub (idempotent) |

## Intégrations : réel vs mock

| Domaine | Mock (par défaut) | Réel (activable) |
|---------|-------------------|------------------|
| Agent runtime | `MockAgentRuntime` (déterministe) | `OpenAICompatibleAgentRuntime` (`AGENT_RUNTIME=openai_compatible` + `LLM_API_KEY`) |
| GitHub | `MockGitHubGateway` | `RealGitHubGateway` (`GITHUB_USER_TOKEN`) |
| Copilot dispatch | `IssueAssignmentDispatcher` (mock confirmé) | `issue_assignment` réel / `agent_tasks_api` (préversion) / `manual` |
| Notifications | `MockNotificationGateway` | `DiscordNotificationGateway` (`DISCORD_BOT_TOKEN`) |
| Déploiement | `MockDeploymentGateway` | `local` / `webhook` |

Voir `docs/runbooks/github-setup.md` et `docs/runbooks/discord-setup.md`.

## Documentation
- Architecture : `docs/architecture/`
- Sécurité : `SECURITY.md`, `docs/security/`
- Parcours & rôles : `docs/functional/`
- Runbooks : `docs/runbooks/`
- ADR : `docs/adr/`
- Suite prévue : `docs/NEXT_STEPS.md`

## Licence
Projet de démonstration interne.

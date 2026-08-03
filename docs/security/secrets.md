# Gestion des secrets

Aucun secret n'est stocké dans le code ou l'historique. Tout provient de
variables d'environnement (voir `.env.example`).

## Tokens GitHub — permissions minimales

### PAT (fine-grained) pour `IssueAssignmentDispatcher`
- **Issues** : Read and write (créer/commenter/affecter).
- **Pull requests** : Read and write (commenter).
- **Contents** : Read (lire le dépôt, checks).
- **Metadata** : Read (obligatoire).

### GitHub App (alternative)
- Permissions : Issues (RW), Pull requests (RW), Checks (R), Contents (R),
  Metadata (R).
- Fournir `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY_PATH`,
  `GITHUB_INSTALLATION_ID`. La clé privée n'est jamais commitée.

### Webhook
- `GITHUB_WEBHOOK_SECRET` partagé, utilisé pour vérifier `X-Hub-Signature-256`.

## Discord
- `DISCORD_BOT_TOKEN` : scope bot, permissions minimales (envoyer des messages,
  utiliser les commandes d'application).
- Ne jamais afficher le token ; les réponses sensibles sont `ephemeral`.

## LLM
- `LLM_API_KEY` : requis uniquement si `AGENT_RUNTIME=openai_compatible`.

## Rotation
- En cas de fuite : révoquer immédiatement le token concerné, en générer un
  nouveau, mettre à jour le secret dans l'environnement / secret manager, et
  auditer `AuditLog` pour les actions récentes.

## Stockage
- Local : fichier `.env` (gitignored).
- CI/CD : secrets GitHub Actions.
- Production : secret manager de la plateforme (jamais dans l'image Docker).

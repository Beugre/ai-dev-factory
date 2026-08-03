# n8n (optionnel)

L'application **fonctionne sans n8n** grâce à ses propres workers. n8n est une
option pour externaliser certaines notifications, webhooks, scénarios
d'intégration, tâches planifiées ou connecteurs externes.

> ⚠️ La logique métier et les états ne vivent **jamais** uniquement dans n8n.
> Le backend reste la source de vérité.

## Workflows versionnés
- `discord-notification-relay.json` : reçoit une notification du backend et la
  relaie vers Discord.

## Activer n8n
1. Lancer une instance n8n (Docker ou cloud).
2. Importer les workflows de ce dossier.
3. Renseigner `N8N_BASE_URL` et `N8N_WEBHOOK_SECRET` dans `.env`.
4. Configurer `DEPLOYMENT_MODE=webhook` et `STAGING_DEPLOY_WEBHOOK_URL` si vous
   souhaitez déclencher des déploiements via n8n.

Aucun secret n'est stocké dans les exports : ils utilisent des variables
d'environnement n8n (`$env`).

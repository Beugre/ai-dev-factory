# Prochaines étapes (NEXT_STEPS)

La V1 livre un vertical slice complet et exécutable en mode mock. Ce document
liste ce qui reste, avec un ordre recommandé.

## Limites connues de la V1
- Le worker est un consommateur Redis léger (BLPOP) plutôt que Celery/Dramatiq.
  Le contrat de job est stable ; la bascule est un remplacement d'adapter.
- L'API OpenAI-compatible et le bot Discord réel nécessitent des credentials
  pour être exercés de bout en bout ; ils sont couverts par des tests unitaires
  et des mocks, pas par un test d'intégration live.
- `GitHubAgenticRuntime` et `AgentTasksApiDispatcher` sont des intégrations en
  préversion, volontairement désactivées et non implémentées end-to-end.
- Les agents Architect / Documentation / Release Manager sont définis (profils +
  prompts) mais ne sont pas encore câblés dans un pipeline automatique côté
  backend (le Product Owner, Reviewer et QA le sont via l'orchestrateur/démo).
- Le traitement des webhooks est synchrone ; pour des charges lourdes, déporter
  vers le worker (le job existe déjà).
- Icônes PWA : `favicon.svg` fourni ; les PNG 192/512 sont référencés dans le
  manifest et à ajouter en binaire.

## TODO explicites dans le code
- `apps/web` : brancher les pages `Agent Runs` et `Delivery` à la navigation
  principale (routes présentes, entrées de menu à compléter).
- Notifications : persister systématiquement chaque `Notification` envoyée
  (actuellement l'envoi mock est tracé en mémoire ; l'entité existe).

## Cinq prochaines stories recommandées
1. **Worker Celery/Dramatiq** : remplacer le worker Redis léger par un broker
   fiable, déporter l'analyse Product Owner et le traitement des webhooks longs.
2. **Persistance des notifications + relances** : enregistrer chaque
   `Notification` avec statut/erreur et rejouer les échecs.
3. **Pipeline agents complet** : enchaîner Architect → Developer(dispatch) →
   Reviewer → QA → Documentation → Release Manager avec `AgentRun` traçables.
4. **Intégration GitHub réelle de bout en bout** : test d'intégration derrière un
   flag avec un dépôt de bac à sable + réception réelle de webhooks.
5. **Bot Discord réel + previews** : déployer le bot, brancher les boutons de
   validation staging et la génération de previews (`DEPLOYMENT_MODE=webhook`).

# Politique de sécurité

## Signaler une vulnérabilité
Ne créez pas d'issue publique décrivant une exploitation. Ouvrez un
« Security finding » (voir `.github/ISSUE_TEMPLATE/security-finding.md`) sans
détails d'exploitation, ou contactez le propriétaire en privé.

## Gestion des secrets
- **Aucun secret** dans le code, les logs ou l'historique Git.
- Tous les secrets proviennent de variables d'environnement (`.env`,
  secret manager). `.env` est ignoré par Git.
- Les logs sont structurés (JSON) et ne contiennent jamais de token.
- Voir `docs/security/secrets.md` pour les permissions minimales des tokens.

## Actions à validation humaine obligatoire
Ces actions ne sont **jamais** automatiques :
- fusion sur la branche principale ;
- déploiement en production ;
- migration destructive ;
- suppression de données ;
- modification des règles de sécurité ;
- utilisation d'un secret non explicitement configuré ;
- action financière ;
- contournement d'une CI en échec.

Le déploiement en **staging** peut être automatisé.

Ces garde-fous sont appliqués dans le domaine/application (ex.
`ApprovalService.ensure_production_approved`, `PullRequestService.approve_staging`
qui bloque si la CI est rouge), pas seulement dans l'interface.

## Contenu non fiable et prompt injection
Tout contenu externe (issues, commentaires, PR, messages Discord, fichiers) est
traité comme **données non fiables**. Les prompts encadrent ce contenu et
interdisent d'en suivre les instructions (changement de rôle, divulgation de
secret, approbation, déploiement, exécution de commande). Des tests couvrent ces
scénarios (`packages/adf/tests/test_prompt_injection.py`).

## Webhooks
Les webhooks GitHub sont vérifiés par signature HMAC SHA-256
(`X-Hub-Signature-256`) et rendus idempotents via le `delivery id`.

## Dépendances
Dependabot surveille pip, npm, GitHub Actions et Docker. Un scan de secrets
(Gitleaks) et un audit des dépendances tournent en CI.

## Modèle de menace
Voir `docs/security/threat-model.md`.

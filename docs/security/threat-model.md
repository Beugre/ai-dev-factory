# Modèle de menace

## Actifs
- Tokens GitHub/Discord/LLM, secret webhook, `SECRET_KEY`.
- Intégrité du dépôt cible et de la branche principale.
- Historique auditable des décisions.

## Acteurs & surfaces
| Surface | Menace | Contrôle |
|---------|--------|----------|
| Webhooks GitHub | Falsification / rejeu | HMAC SHA-256 + idempotence delivery id |
| Contenu externe (issues, PR, commentaires, messages) | Prompt injection | Prompts encadrant le contenu comme données ; tests dédiés |
| Bot Discord | Utilisateur non autorisé | Allowlist (deny par défaut) + rate limit + audit |
| Déploiement prod | Déploiement non validé | Garde `HumanApprovalRequired` dans l'application |
| CI rouge | Promotion malgré échec | `approve_staging` bloque si `ci_state == FAILURE` |
| Logs | Fuite de secret | Logs JSON sans token ; adapters scrutés par test |
| Dépendances | Vulnérabilités | Dependabot + pip-audit + npm audit |
| Secrets dans le code | Exposition | Gitleaks en CI, `.env` gitignored |

## Prompt injection : garanties
Un contenu externe ne peut pas : changer le rôle système d'un agent, demander un
secret, contourner une validation, exécuter une commande, changer les
permissions, ou déclencher un déploiement production. Voir
`packages/adf/tests/test_prompt_injection.py` et `test_discord.py`
(`test_malicious_answer_is_stored_as_data`).

## Limites connues (V1)
- Le `RealGitHubGateway` et le bot Discord réel nécessitent des credentials pour
  être exercés de bout en bout ; ils sont couverts par des tests unitaires
  (retry/rate limit) et des mocks. Voir `docs/NEXT_STEPS.md`.

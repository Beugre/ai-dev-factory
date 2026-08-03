# Rôles

## Rôles humains
| Rôle | Responsabilités | Actions réservées |
|------|-----------------|-------------------|
| Propriétaire | Décrit les besoins, valide périmètre/staging/production | Toutes les validations sensibles |
| Reviewer humain | Revue finale avant fusion | Fusion sur `main` |

## Rôles agents (IA)
| Agent | Rôle | Ne fait pas |
|-------|------|-------------|
| Product Owner | Analyse, questions, epic, stories, Gherkin | Écrire du code de production |
| Architect | Impacts, interfaces, migrations, ADR | Surconcevoir |
| Developer | Implémente une story, tests, doc | Fusionner sa PR, ignorer la CI |
| Reviewer | Revue structurée | Modifier le code (sauf demande) |
| QA | Scénarios de test, verdict | Inventer des exigences |
| Documentation | Docs, diagrammes, ADR, runbooks | Documenter l'inexistant |
| Release Manager | CI, release notes, staging | Déployer en prod sans validation |

## Frontière de confiance
Les agents opèrent sur des données potentiellement non fiables. Aucune décision
sensible n'est prise sans validation humaine explicite, appliquée dans le
domaine/application.

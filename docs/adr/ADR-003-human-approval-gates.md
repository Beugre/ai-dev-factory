# ADR-003 — Portes de validation humaine

## Statut
Accepté.

## Contexte
L'IA exécute le travail, mais certaines actions sont irréversibles ou sensibles
et ne doivent jamais être automatiques.

## Décision
Les garde-fous sont appliqués dans le **domaine/application**, pas seulement
dans l'UI :
- Transitions d'état validées par `domain/state_machine` ; toute transition
  invalide lève `InvalidStateTransition`.
- `PullRequestService.approve_staging` **bloque si `ci_state == FAILURE`**
  (`CIFailure`).
- `ApprovalService.ensure_production_approved` lève `HumanApprovalRequired` tant
  qu'aucune approbation `PRODUCTION` n'existe.
- Le staging peut être automatisé ; la production exige une approbation humaine.
- Chaque action agentique/sensible est auditée (`AuditLog`).

## Actions à validation humaine obligatoire
Fusion sur `main`, déploiement production, migration destructive, suppression de
données, changement de règles de sécurité, usage d'un secret non configuré,
action financière, contournement d'une CI en échec.

## Conséquences
- Impossible de contourner ces règles via l'API ou l'UI.
- Tests dédiés : `test_production_gate.py`, `test_pull_request.py`.

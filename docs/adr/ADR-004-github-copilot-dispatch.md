# ADR-004 — Stratégies de dispatch Copilot

## Statut
Accepté.

## Contexte
L'affectation du développement à GitHub Copilot dépend du compte, du forfait et
d'API parfois en préversion. Le projet doit rester fonctionnel dans tous les cas
et ne jamais mentir sur le succès d'une affectation.

## Décision
Un port `CopilotDispatcher` avec trois stratégies, sélectionnées par
`COPILOT_DISPATCH_MODE` :
- `issue_assignment` — affecte `copilot-swe-agent[bot]` à l'issue ; le succès
  n'est confirmé que si GitHub renvoie le bot dans les assignees.
- `agent_tasks_api` — API de tâches d'agent GitHub (**préversion**), désactivée
  par défaut ; échoue explicitement si activée sans être disponible.
- `manual` — laisse l'issue prête à être affectée manuellement.

`DispatchResult.confirmed` reflète l'état réel. On ne prétend jamais qu'une
affectation a réussi sans confirmation.

## Conséquences
- Repli déterministe (`manual`) toujours disponible.
- Tests : `test_dispatch.py` (confirmation mock, fallback, API préversion off).
- Les instructions/agent/modèle sont transmis quand l'API le permet, sinon
  portés par le corps de l'issue.

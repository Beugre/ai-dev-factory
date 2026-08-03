# ADR-002 — Agent runtime abstrait

## Statut
Accepté.

## Contexte
Le domaine ne doit dépendre d'aucun fournisseur de modèle IA. Il faut démontrer
tout le workflow sans clé API, tout en permettant un LLM réel.

## Décision
- Port `AgentRuntime` (`adf/ports/agent_runtime.py`) : exécute un agent avec
  rôle, instructions, contexte, schéma de sortie, `correlation_id`, timeout,
  politique de retry.
- Sorties **structurées et validées par Pydantic** (`adf/domain/contracts.py`).
  Une sortie malformée lève avant toute persistance (frontière de sécurité).
- Implémentations :
  - `MockAgentRuntime` — déterministe, obligatoire, alimente `make demo`.
  - `OpenAICompatibleAgentRuntime` — endpoints compatibles Chat Completions.
  - `GitHubAgenticRuntime` — préversion, derrière feature flag, non requise.

## Conséquences
- Le workflow complet est testable hors-ligne.
- Changer de fournisseur = changer un adapter, pas le domaine.
- Les prompts sont versionnés et encadrent les contenus non fiables.

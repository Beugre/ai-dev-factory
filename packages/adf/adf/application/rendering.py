"""Helpers to render domain contracts into human-readable text."""

from __future__ import annotations

from adf.domain.contracts import GherkinScenario, StoryContract


def render_gherkin(scenarios: list[GherkinScenario]) -> str:
    blocks: list[str] = []
    for scenario in scenarios:
        lines = [f"Scenario: {scenario.title}"]
        lines.extend(f"  {step}" for step in scenario.steps)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def render_story_issue_body(story: StoryContract, *, context: str) -> str:
    """Build the standard story issue body required by the templates."""
    criteria = "\n".join(f"- {c}" for c in story.acceptance_criteria) or "- (à définir)"
    deps = "\n".join(f"- {d}" for d in story.dependencies) or "- Aucune"
    gherkin = render_gherkin(story.gherkin) or "_(aucun scénario)_"
    return f"""## Contexte

{context}

## Besoin utilisateur

{story.description}

## Périmètre

{story.title}

## Hors périmètre

- Tout ce qui n'est pas listé dans les critères d'acceptation.

## Règles métier

{criteria}

## Critères d'acceptation

{criteria}

## Scénarios Gherkin

```gherkin
{gherkin}
```

## Impacts techniques connus

- À compléter par l'agent Architecte si nécessaire.

## Dépendances

{deps}

## Tests attendus

- Tests unitaires couvrant les critères d'acceptation.
- Tests d'erreur et de droits.

## Definition of Done

- [ ] Critères d'acceptation satisfaits
- [ ] Tests écrits et passants
- [ ] Lint et typecheck OK
- [ ] Documentation mise à jour
- [ ] Revue humaine effectuée
"""

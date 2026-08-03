---
applyTo: ".github/workflows/**"
---

# Instructions GitHub Actions

- Principe du **moindre privilège** : déclarer `permissions:` au plus juste
  (par défaut `contents: read`).
- **Épingler** les actions à une version stable (tag `@vX` au minimum).
- Ne jamais exposer de secret aux workflows déclenchés depuis un fork
  (`pull_request_target` interdit sans revue de sécurité).
- Séparer les jobs (lint, typecheck, tests, build) pour un feedback rapide.
- Le workflow de production reste **désactivé par défaut** et protégé par un
  environnement GitHub nécessitant une approbation.
- Ne jamais contourner une CI en échec.

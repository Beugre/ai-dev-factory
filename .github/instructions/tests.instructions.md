---
applyTo: "**/tests/**"
---

# Instructions Tests

- Un test doit être déterministe et indépendant des services externes.
- Backend : utiliser les adapters mock et une base SQLite temporaire isolée
  (fixture `_isolated_db`). Marqueurs : `integration`, `e2e`.
- Couvrir : cas nominal, cas d'erreur, droits, concurrence quand pertinent.
- Toujours tester les transitions d'état invalides (doivent lever une erreur).
- Toujours tester la résistance aux prompt injections et la non-divulgation de
  secrets pour tout nouveau chemin agentique.
- Frontend : tester le rendu et le comportement, pas l'implémentation interne.
- Ne pas viser artificiellement 100 % de couverture : viser une couverture utile.

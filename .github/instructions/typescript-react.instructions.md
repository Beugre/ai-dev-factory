---
applyTo: "apps/web/**/*.{ts,tsx}"
---

# Instructions TypeScript / React

- TypeScript strict. Pas de `any`.
- Composants fonctionnels + hooks. Pas de logique métier critique dans les
  composants : elle vit dans le backend.
- Données serveur via TanStack Query (`src/lib/queries.ts`).
- Formulaires via React Hook Form + validation Zod.
- Styles via Tailwind ; design mobile-first, mode sombre, pensé « pouce ».
- Noms techniques en anglais ; **textes de l'interface en français**.
- Accessibilité : rôles ARIA et labels sur les actions.
- Tests : Vitest + Testing Library (`apps/web/tests`), e2e Playwright
  (`apps/web/e2e`).
- Ne jamais stocker de secret côté client.

# Tests end-to-end

Les tests e2e de l'interface web utilisent Playwright et vivent dans
`apps/web/e2e`. Ils nécessitent la stack lancée (API + web).

```bash
docker compose up --build        # ou make up
cd apps/web && npm run test:e2e
```

Le parcours e2e « backend » (mock complet) est couvert par
`tests/integration/test_demo_integration.py` et
`packages/adf/tests/test_demo_e2e.py`.

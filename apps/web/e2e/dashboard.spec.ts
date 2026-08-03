import { expect, test } from '@playwright/test';

// Requires the stack running (docker compose up) with the demo project seeded.
test('dashboard loads and navigation works', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Pilotage' })).toBeVisible();
    await page.getByRole('link', { name: /Créer/ }).click();
    await expect(page.getByRole('heading', { name: 'Nouvelle demande' })).toBeVisible();
});

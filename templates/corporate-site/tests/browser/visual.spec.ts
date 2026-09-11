import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
const content = JSON.parse(readFileSync(new URL('../../src/content/site.json', import.meta.url), 'utf8'));
for (const width of [1440, 390, 320]) {
  test(`visual structure and local-only boundaries ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 960 });
    const external: string[] = [], errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/*', route => {
      if (new URL(route.request().url()).hostname !== '127.0.0.1') {
        external.push(route.request().url()); return route.abort();
      }
      return route.continue();
    });
    await page.goto('/');
    await expect(page).toHaveTitle(`${content.brand.name} · Vista previa`);
    await expect(page.locator('h1')).toHaveCount(1);
    await expect(page.locator('h1')).toContainText(content.hero.title);
    await expect(page.locator('main')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const anchors = await page.locator('a[href^="#"]').evaluateAll(elements => elements.map(e => e.getAttribute('href')!.slice(1)));
    for (const id of anchors) await expect(page.locator(`[id="${id}"]`)).toHaveCount(1);
    await expect(page.locator('#domain')).toBeEnabled();
    await expect(page.getByRole('dialog')).not.toBeVisible();
    await expect(page.locator('form[action]')).toHaveCount(0);
    await expect(page.getByText('No se ha enviado ninguna consulta. La información permanece solo en esta página hasta recargarla.', { exact: true })).toBeVisible();
    await page.locator('#preguntas summary').first().focus();
    await page.keyboard.press('Enter');
    await expect(page.locator('#preguntas details').first()).toHaveAttribute('open', '');
    await expect(page.locator('#preguntas details').first().locator('p')).toBeVisible();
    if (width < 1050) {
      await page.getByText('Menú', { exact: true }).click();
      await expect(page.getByRole('navigation', { name: 'Principal móvil' })).toBeVisible();
      await page.getByText('Menú', { exact: true }).click();
    }
    await page.emulateMedia({ reducedMotion: 'reduce' });
    expect(await page.evaluate(() => getComputedStyle(document.documentElement).scrollBehavior)).toBe('auto');
    expect(external).toEqual([]); expect(errors).toEqual([]);
    await page.screenshot({ path: `test-results/landing-${width}.png`, fullPage: true });
  });
}

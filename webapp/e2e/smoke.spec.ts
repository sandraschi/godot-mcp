import { test, expect } from '@playwright/test';
const BE = 'http://127.0.0.1:10993';
const FE = 'http://127.0.0.1:10992';

test.describe('Fleet Audit', () => {
  test('Backend health returns 200', async ({ request }) => {
    const resp = await request.get(BE + '/health');
    expect(resp.status()).toBe(200);
  });

  test('Backend diagnostics returns tool_count', async ({ request }) => {
    const resp = await request.get(BE + '/api/v1/diagnostics');
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body).toHaveProperty('tool_count');
    expect(typeof body.tool_count).toBe('number');
    expect(body.tool_count).toBeGreaterThan(0);
    expect(body).toHaveProperty('status', 'ok');
  });

  test('Backend capabilities endpoint', async ({ request }) => {
    const resp = await request.get(BE + '/api/capabilities');
    expect(resp.status()).toBe(200);
  });

  test('Frontend loads without console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.goto(FE, { timeout: 15000 });
    await page.waitForTimeout(3000);
    await expect(page.locator('#root')).toBeAttached();
    expect(errors.filter(e => !e.includes('favicon'))).toEqual([]);
  });

  test('Sidebar navigation is visible', async ({ page }) => {
    await page.goto(FE, { timeout: 15000 });
    await page.waitForTimeout(3000);
    const sidebar = page.locator('nav, aside, [class*="sidebar"]');
    await expect(sidebar.first()).toBeAttached({ timeout: 5000 });
  });

  test('Page navigation does not 404', async ({ page, context }) => {
    const responses: string[] = [];
    context.on('response', response => {
      if (response.status() === 404) responses.push(response.url());
    });
    await page.goto(FE, { timeout: 15000 });
    await page.waitForTimeout(3000);
    const routes = ['/', '/tools', '/skills', '/chat', '/logs', '/help', '/models', '/projects', '/depot', '/bundles'];
    for (const route of routes) {
      await page.goto(FE + route, { timeout: 15000, waitUntil: 'networkidle' });
      await page.waitForTimeout(1000);
    }
    expect(responses.filter(r => !r.includes('favicon'))).toEqual([]);
  });

  test('Dashboard has KPIs', async ({ page }) => {
    await page.goto(FE, { timeout: 15000 });
    await page.waitForTimeout(3000);
    const kpis = page.locator('[class*="kpi"], [class*="stat"], [class*="metric"], [class*="card"]');
    const count = await kpis.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('Post invalid input returns 422', async ({ request }) => {
    const resp = await request.post(BE + '/api/v1/control/tool', { data: {} });
    expect([400, 422]).toContain(resp.status());
  });
});

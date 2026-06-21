import { defineConfig } from '@playwright/test';
export default defineConfig({
    testDir: './e2e', timeout: 60000, retries: 1,
    use: { baseURL: 'http://localhost:10992', headless: true, screenshot: 'only-on-failure' },
    webServer: {
        command: 'uv run python -m godot_mcp.server --port 10993',
        port: 10993, timeout: 30000, reuseExistingServer: false
    }
});

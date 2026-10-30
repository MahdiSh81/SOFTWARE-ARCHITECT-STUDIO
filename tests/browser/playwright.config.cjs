const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
 testDir: '.', testMatch: '*.spec.cjs', timeout: 30000, expect: { timeout: 5000 }, fullyParallel: true, reporter: 'list',
 use: { baseURL: 'http://127.0.0.1:4173', browserName: 'chromium', headless: true, trace: 'retain-on-failure' },
 webServer: { command: 'python serve_workbench.py', url: 'http://127.0.0.1:4173/workbench/index.html', reuseExistingServer: !process.env.CI, timeout: 15000 }
});

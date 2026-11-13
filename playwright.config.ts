import { defineConfig } from '@playwright/test';
export default defineConfig({
 testDir:'web/tests',timeout:60000,workers:1,
 use:{baseURL:'http://127.0.0.1:8787',headless:true,launchOptions:{executablePath:process.env.FETCH_BROWSER_EXECUTABLE ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'}},
 webServer:{command:'.venv/bin/python scripts/browser_fixture.py',url:'http://127.0.0.1:8787/api/v1/health',reuseExistingServer:true,timeout:20000},
});

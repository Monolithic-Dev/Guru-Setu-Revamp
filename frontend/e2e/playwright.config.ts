// TEST-54 primary-flow smoke (optional, T6.P3.2). Runs against the real stack, not mocks:
//   docker compose up -d && docker compose exec backend python -m scripts.seed --reset
//   npm --prefix frontend run e2e            (E2E_BASE_URL defaults to http://localhost:3000)
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  timeout: 120_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0, // flaky-test policy: no automatic retries (test-strategy §7)
  reporter: [["list"]],
  outputDir: "../test-results",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } }],
});

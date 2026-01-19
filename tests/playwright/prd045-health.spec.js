/**
 * Playwright UI Tests for PRD-045 Health Monitoring Widget
 *
 * Tests the health widget UI interactions:
 * - Health widget presence in header
 * - Health indicator dot colors
 * - Dropdown toggle behavior
 * - Source health rendering
 * - Alert display and acknowledgment
 * - Refresh functionality
 */

const { test, expect } = require('@playwright/test');

// Mock API responses
const mockHealthyResponse = {
    sources: {
        youtube: {
            status: 'healthy',
            last_collection: new Date().toISOString(),
            items_24h: 15,
            errors_24h: 0,
            consecutive_failures: 0,
            is_stale: false,
            message: 'Operating normally',
            transcription: {
                pending: 0,
                completed: 15,
                failed: 0
            }
        },
        discord: {
            status: 'healthy',
            last_collection: new Date().toISOString(),
            items_24h: 42,
            errors_24h: 0,
            consecutive_failures: 0,
            is_stale: false,
            message: 'Operating normally',
            transcription: {
                pending: 1,
                completed: 10,
                failed: 0
            }
        },
        '42macro': {
            status: 'healthy',
            last_collection: new Date().toISOString(),
            items_24h: 8,
            errors_24h: 0,
            consecutive_failures: 0,
            is_stale: false,
            message: 'Operating normally',
            transcription: {
                pending: 0,
                completed: 8,
                failed: 0
            }
        },
        substack: {
            status: 'healthy',
            last_collection: new Date().toISOString(),
            items_24h: 5,
            errors_24h: 0,
            consecutive_failures: 0,
            is_stale: false,
            message: 'Operating normally'
        },
        kt_technical: {
            status: 'healthy',
            last_collection: new Date().toISOString(),
            items_24h: 3,
            errors_24h: 0,
            consecutive_failures: 0,
            is_stale: false,
            message: 'Operating normally'
        }
    },
    overall_status: 'healthy',
    alerts: [],
    timestamp: new Date().toISOString()
};

const mockDegradedResponse = {
    sources: {
        youtube: {
            status: 'stale',
            last_collection: new Date(Date.now() - 72 * 60 * 60 * 1000).toISOString(),
            items_24h: 0,
            errors_24h: 0,
            consecutive_failures: 0,
            is_stale: true,
            message: 'No new content in 48+ hours',
            transcription: {
                pending: 5,
                completed: 10,
                failed: 2,
                backlog: 5
            }
        },
        discord: {
            status: 'healthy',
            last_collection: new Date().toISOString(),
            items_24h: 42,
            errors_24h: 0,
            consecutive_failures: 0,
            is_stale: false,
            message: 'Operating normally'
        }
    },
    overall_status: 'degraded',
    alerts: [
        {
            id: 1,
            type: 'source_stale',
            source: 'youtube',
            severity: 'medium',
            message: 'No new content from youtube in 72 hours',
            created_at: new Date().toISOString()
        },
        {
            id: 2,
            type: 'transcription_backlog',
            source: 'youtube',
            severity: 'high',
            message: '5 youtube videos pending transcription for >24 hours',
            created_at: new Date().toISOString()
        }
    ],
    timestamp: new Date().toISOString()
};

const mockCriticalResponse = {
    sources: {
        youtube: {
            status: 'critical',
            last_collection: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
            items_24h: 0,
            errors_24h: 8,
            consecutive_failures: 3,
            is_stale: true,
            message: '3 consecutive collection failures'
        },
        discord: {
            status: 'critical',
            last_collection: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
            items_24h: 0,
            errors_24h: 5,
            consecutive_failures: 2,
            is_stale: true,
            message: '2 consecutive collection failures'
        }
    },
    overall_status: 'critical',
    alerts: [
        {
            id: 3,
            type: 'collection_failed',
            source: 'youtube',
            severity: 'critical',
            message: 'youtube has failed 3 consecutive collections',
            created_at: new Date().toISOString()
        }
    ],
    timestamp: new Date().toISOString()
};

test.describe('PRD-045 Health Widget', () => {

    test.describe('Widget Presence', () => {

        test('health widget exists in header', async ({ page }) => {
            // Mock the health API
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockHealthyResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-widget', { timeout: 5000 });

            const widget = page.locator('#health-widget');
            await expect(widget).toBeVisible();
        });

        test('health indicator button is clickable', async ({ page }) => {
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockHealthyResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-indicator', { timeout: 5000 });

            const indicator = page.locator('#health-indicator');
            await expect(indicator).toBeVisible();
            await expect(indicator).toBeEnabled();
        });

        test('health dot shows correct status color', async ({ page }) => {
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockHealthyResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-dot', { timeout: 5000 });

            const dot = page.locator('#health-dot');
            await expect(dot).toHaveClass(/health-healthy/);
        });

    });

    test.describe('Dropdown Behavior', () => {

        test('dropdown opens on click', async ({ page }) => {
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockHealthyResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-indicator', { timeout: 5000 });

            // Click indicator
            await page.click('#health-indicator');

            // Dropdown should be visible
            const dropdown = page.locator('#health-dropdown');
            await expect(dropdown).toHaveClass(/show/);
        });

        test('dropdown closes on outside click', async ({ page }) => {
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockHealthyResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-indicator', { timeout: 5000 });

            // Open dropdown
            await page.click('#health-indicator');
            await page.waitForSelector('#health-dropdown.show', { timeout: 2000 });

            // Click outside
            await page.click('body', { position: { x: 10, y: 10 } });

            // Dropdown should be hidden
            const dropdown = page.locator('#health-dropdown');
            await expect(dropdown).not.toHaveClass(/show/);
        });

        test('dropdown shows sources list', async ({ page }) => {
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockHealthyResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-indicator', { timeout: 5000 });

            // Open dropdown
            await page.click('#health-indicator');
            await page.waitForSelector('#health-dropdown.show', { timeout: 2000 });

            // Check for source items
            const content = page.locator('#health-dropdown-content');
            await expect(content).toContainText('YouTube');
            await expect(content).toContainText('Discord');
        });

    });

    test.describe('Status Indicators', () => {

        test('shows healthy status correctly', async ({ page }) => {
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockHealthyResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-dot', { timeout: 5000 });

            const dot = page.locator('#health-dot');
            await expect(dot).toHaveClass(/health-healthy/);
        });

        test('shows degraded status correctly', async ({ page }) => {
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockDegradedResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-dot', { timeout: 5000 });

            const dot = page.locator('#health-dot');
            await expect(dot).toHaveClass(/health-degraded/);
        });

        test('shows critical status correctly', async ({ page }) => {
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockCriticalResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-dot', { timeout: 5000 });

            const dot = page.locator('#health-dot');
            await expect(dot).toHaveClass(/health-critical/);
        });

    });

    test.describe('Alerts Display', () => {

        test('shows alerts section when alerts exist', async ({ page }) => {
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockDegradedResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-indicator', { timeout: 5000 });

            // Open dropdown
            await page.click('#health-indicator');
            await page.waitForSelector('#health-dropdown.show', { timeout: 2000 });

            // Alerts section should be visible
            const alertsSection = page.locator('#health-alerts-section');
            await expect(alertsSection).toBeVisible();
        });

        test('hides alerts section when no alerts', async ({ page }) => {
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockHealthyResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-indicator', { timeout: 5000 });

            // Open dropdown
            await page.click('#health-indicator');
            await page.waitForSelector('#health-dropdown.show', { timeout: 2000 });

            // Alerts section should be hidden
            const alertsSection = page.locator('#health-alerts-section');
            await expect(alertsSection).toBeHidden();
        });

        test('displays alert details correctly', async ({ page }) => {
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockDegradedResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-indicator', { timeout: 5000 });

            // Open dropdown
            await page.click('#health-indicator');
            await page.waitForSelector('#health-dropdown.show', { timeout: 2000 });

            // Check alert content
            const alertsList = page.locator('#health-alerts-list');
            await expect(alertsList).toContainText('youtube');
            await expect(alertsList).toContainText('MEDIUM');
        });

    });

    test.describe('Refresh Functionality', () => {

        test('refresh button exists', async ({ page }) => {
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockHealthyResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-indicator', { timeout: 5000 });

            // Open dropdown
            await page.click('#health-indicator');
            await page.waitForSelector('#health-dropdown.show', { timeout: 2000 });

            const refreshBtn = page.locator('#health-refresh-btn');
            await expect(refreshBtn).toBeVisible();
        });

        test('refresh button triggers API call', async ({ page }) => {
            let apiCallCount = 0;

            await page.route('**/api/health/sources', route => {
                apiCallCount++;
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockHealthyResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-indicator', { timeout: 5000 });

            // Open dropdown
            await page.click('#health-indicator');
            await page.waitForSelector('#health-dropdown.show', { timeout: 2000 });

            const initialCalls = apiCallCount;

            // Click refresh
            await page.click('#health-refresh-btn');

            // Wait for API call
            await page.waitForTimeout(1000);

            expect(apiCallCount).toBeGreaterThan(initialCalls);
        });

    });

    test.describe('Transcription Status', () => {

        test('shows transcription stats for video sources', async ({ page }) => {
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockHealthyResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-indicator', { timeout: 5000 });

            // Open dropdown
            await page.click('#health-indicator');
            await page.waitForSelector('#health-dropdown.show', { timeout: 2000 });

            // Check for transcription info
            const content = page.locator('#health-dropdown-content');
            // YouTube has transcription data
            await expect(content).toContainText('Transcripts');
        });

        test('shows backlog warning when present', async ({ page }) => {
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockDegradedResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-indicator', { timeout: 5000 });

            // Open dropdown
            await page.click('#health-indicator');
            await page.waitForSelector('#health-dropdown.show', { timeout: 2000 });

            // Check for backlog warning
            const content = page.locator('#health-dropdown-content');
            await expect(content).toContainText('backlog');
        });

    });

    test.describe('Accessibility', () => {

        test('health indicator has title attribute', async ({ page }) => {
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockHealthyResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-indicator', { timeout: 5000 });

            const indicator = page.locator('#health-indicator');
            await expect(indicator).toHaveAttribute('title', /health/i);
        });

        test('refresh button has title attribute', async ({ page }) => {
            await page.route('**/api/health/sources', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockHealthyResponse)
                });
            });

            await page.goto('/');
            await page.waitForSelector('#health-indicator', { timeout: 5000 });

            // Open dropdown
            await page.click('#health-indicator');
            await page.waitForSelector('#health-dropdown.show', { timeout: 2000 });

            const refreshBtn = page.locator('#health-refresh-btn');
            await expect(refreshBtn).toHaveAttribute('title', /refresh/i);
        });

    });

});

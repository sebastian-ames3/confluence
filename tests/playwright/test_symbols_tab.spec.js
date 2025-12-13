/**
 * Playwright UI Tests for PRD-039 Symbols Tab
 *
 * Tests the Symbols tab UI interactions:
 * - Tab navigation
 * - Symbol list rendering
 * - Symbol card clicks
 * - Detail modal display
 * - Price levels table
 * - Confluence indicators
 * - Staleness warnings
 */

const { test, expect } = require('@playwright/test');

// Mock API responses
const mockSymbolsResponse = {
    symbols: [
        {
            symbol: 'GOOGL',
            kt_view: {
                bias: 'bullish',
                wave_position: 'wave_5',
                wave_phase: 'impulse',
                is_stale: false,
                last_updated: new Date().toISOString()
            },
            discord_view: {
                quadrant: 'buy_call',
                iv_regime: 'normal',
                is_stale: false,
                last_updated: new Date().toISOString()
            },
            confluence: {
                score: 0.85,
                aligned: true
            },
            active_levels_count: 6
        },
        {
            symbol: 'SPX',
            kt_view: {
                bias: 'bullish',
                wave_position: 'wave_3',
                wave_phase: 'impulse',
                is_stale: false,
                last_updated: new Date().toISOString()
            },
            discord_view: {
                quadrant: 'buy_call',
                iv_regime: 'elevated',
                is_stale: false,
                last_updated: new Date().toISOString()
            },
            confluence: {
                score: 0.75,
                aligned: true
            },
            active_levels_count: 3
        },
        {
            symbol: 'IWM',
            kt_view: {
                bias: 'neutral',
                wave_position: 'wave_A',
                wave_phase: 'correction',
                is_stale: false,
                last_updated: new Date().toISOString()
            },
            discord_view: {
                quadrant: 'N/A',
                is_stale: true,
                last_updated: new Date(Date.now() - 16 * 24 * 60 * 60 * 1000).toISOString()  // 16 days ago
            },
            confluence: {
                score: 0.35,
                aligned: false
            },
            active_levels_count: 5
        }
    ]
};

const mockSymbolDetailResponse = {
    symbol: 'GOOGL',
    kt_technical: {
        wave_position: 'wave_5',
        wave_direction: 'up',
        wave_phase: 'impulse',
        wave_degree: 'intermediate',
        bias: 'bullish',
        primary_target: 328.0,
        primary_support: 319.0,
        invalidation: 270.0,
        notes: 'Wave 5 targeting 328-330 zone',
        last_updated: new Date().toISOString(),
        kt_is_stale: false
    },
    discord_options: {
        quadrant: 'buy_call',
        iv_regime: 'normal',
        strategy_rec: 'Bullish call spreads',
        notes: 'Favorable risk/reward for upside',
        last_updated: new Date().toISOString(),
        discord_is_stale: false
    },
    confluence: {
        score: 0.85,
        aligned: true,
        summary: 'Both KT Technical and Discord Options indicate bullish bias',
        trade_setup: 'Consider call spreads targeting 328 with stops below 310'
    },
    levels: [
        {
            id: 1,
            price: 328.0,
            price_upper: 330.0,
            type: 'target',
            direction: 'neutral',
            source: 'kt_technical',
            fib_level: null,
            context_snippet: 'targets for wave 5 completion are looking at 328 to 330 zone',
            confidence: 0.8,
            is_stale: false
        },
        {
            id: 2,
            price: 319.0,
            type: 'support',
            direction: 'bullish_reversal',
            source: 'kt_technical',
            fib_level: '0.236',
            context_snippet: 'support likely holding at the 0.236 fib level around 319',
            confidence: 0.85,
            is_stale: false
        },
        {
            id: 3,
            price: 313.0,
            type: 'support',
            direction: 'bullish_reversal',
            source: 'kt_technical',
            fib_level: '0.382',
            context_snippet: 'the 0.382 fib at 313 should provide solid support',
            confidence: 0.85,
            is_stale: false
        },
        {
            id: 4,
            price: 308.0,
            type: 'support',
            direction: 'bullish_reversal',
            source: 'kt_technical',
            fib_level: '0.5',
            context_snippet: 'The 0.5 fib sits at 308',
            confidence: 0.75,
            is_stale: false
        },
        {
            id: 5,
            price: 270.0,
            type: 'invalidation',
            direction: 'bearish_breakdown',
            source: 'kt_technical',
            fib_level: null,
            context_snippet: 'real invalidation is below 270 where weekly demand breaks',
            confidence: 0.9,
            is_stale: false
        }
    ]
};

test.describe('Symbols Tab', () => {
    test.beforeEach(async ({ page }) => {
        // Mock API responses
        await page.route('**/api/symbols', async route => {
            await route.fulfill({ json: mockSymbolsResponse });
        });

        await page.route('**/api/symbols/GOOGL', async route => {
            await route.fulfill({ json: mockSymbolDetailResponse });
        });

        // Mock other required endpoints
        await page.route('**/api/synthesis/status/overview', async route => {
            await route.fulfill({ json: { total_content_24h: 10, total_content_7d: 50, sources_status: [] } });
        });

        await page.route('**/api/synthesis/latest', async route => {
            await route.fulfill({ json: { status: 'not_found' } });
        });

        await page.route('**/api/themes/summary', async route => {
            await route.fulfill({ json: { total: 5, by_status: { active: 3 } } });
        });

        // Navigate to the page
        await page.goto('http://localhost:8000');
    });

    test('should display Symbols tab button', async ({ page }) => {
        const symbolsTab = page.locator('button[data-tab="symbols"]');
        await expect(symbolsTab).toBeVisible();
        await expect(symbolsTab).toHaveText('Symbols');
    });

    test('should switch to Symbols tab on click', async ({ page }) => {
        const symbolsTab = page.locator('button[data-tab="symbols"]');
        await symbolsTab.click();

        // Check tab is active
        await expect(symbolsTab).toHaveClass(/active/);

        // Check panel is visible
        const symbolsPanel = page.locator('#panel-symbols');
        await expect(symbolsPanel).toBeVisible();
    });

    test('should load and display symbol list', async ({ page }) => {
        // Switch to Symbols tab
        await page.locator('button[data-tab="symbols"]').click();

        // Wait for symbols to load
        await page.waitForSelector('.symbols-grid');

        // Check that symbol cards are rendered
        const symbolCards = page.locator('.symbol-card');
        await expect(symbolCards).toHaveCount(3);

        // Check GOOGL card
        const googlCard = page.locator('.symbol-card[data-symbol="GOOGL"]');
        await expect(googlCard).toBeVisible();
        await expect(googlCard).toContainText('GOOGL');
        await expect(googlCard).toContainText('6 levels');
    });

    test('should display confluence indicators correctly', async ({ page }) => {
        await page.locator('button[data-tab="symbols"]').click();
        await page.waitForSelector('.symbols-grid');

        // Check GOOGL high confluence
        const googlCard = page.locator('.symbol-card[data-symbol="GOOGL"]');
        const googlConfluence = googlCard.locator('.symbol-confluence');
        await expect(googlConfluence).toHaveClass(/confluence-high/);
        await expect(googlConfluence).toContainText('High Confluence');
        await expect(googlConfluence).toContainText('85%');

        // Check IWM low confluence
        const iwmCard = page.locator('.symbol-card[data-symbol="IWM"]');
        const iwmConfluence = iwmCard.locator('.symbol-confluence');
        await expect(iwmConfluence).toHaveClass(/confluence-low/);
        await expect(iwmConfluence).toContainText('Low Confluence');
        await expect(iwmConfluence).toContainText('35%');
    });

    test('should display staleness indicators', async ({ page }) => {
        await page.locator('button[data-tab="symbols"]').click();
        await page.waitForSelector('.symbols-grid');

        // IWM has stale Discord data
        const iwmCard = page.locator('.symbol-card[data-symbol="IWM"]');
        const staleIndicator = iwmCard.locator('.stale-indicator');
        await expect(staleIndicator).toBeVisible();
        await expect(staleIndicator).toHaveAttribute('title', 'Data is stale');
    });

    test('should open detail modal on card click', async ({ page }) => {
        await page.locator('button[data-tab="symbols"]').click();
        await page.waitForSelector('.symbols-grid');

        // Click GOOGL card
        const googlCard = page.locator('.symbol-card[data-symbol="GOOGL"]');
        await googlCard.click();

        // Wait for modal to appear
        const modal = page.locator('#symbol-detail-modal');
        await expect(modal).toHaveClass(/active/);

        // Check modal content
        const modalContent = page.locator('#symbol-detail-content');
        await expect(modalContent).toContainText('GOOGL');
    });

    test('should display KT Technical section in detail modal', async ({ page }) => {
        await page.locator('button[data-tab="symbols"]').click();
        await page.waitForSelector('.symbols-grid');
        await page.locator('.symbol-card[data-symbol="GOOGL"]').click();

        await page.waitForSelector('#symbol-detail-content');

        // Check KT Technical section
        const modalContent = page.locator('#symbol-detail-content');
        await expect(modalContent).toContainText('KT Technical');
        await expect(modalContent).toContainText('Wave: wave_5');
        await expect(modalContent).toContainText('Bias: bullish');
        await expect(modalContent).toContainText('Target: 328');
        await expect(modalContent).toContainText('Support: 319');
        await expect(modalContent).toContainText('Invalidation: 270');
    });

    test('should display Discord Options section in detail modal', async ({ page }) => {
        await page.locator('button[data-tab="symbols"]').click();
        await page.waitForSelector('.symbols-grid');
        await page.locator('.symbol-card[data-symbol="GOOGL"]').click();

        await page.waitForSelector('#symbol-detail-content');

        // Check Discord Options section
        const modalContent = page.locator('#symbol-detail-content');
        await expect(modalContent).toContainText('Discord Options');
        await expect(modalContent).toContainText('Quadrant: buy_call');
        await expect(modalContent).toContainText('IV Regime: normal');
        await expect(modalContent).toContainText('Strategy: Bullish call spreads');
    });

    test('should display price levels table in detail modal', async ({ page }) => {
        await page.locator('button[data-tab="symbols"]').click();
        await page.waitForSelector('.symbols-grid');
        await page.locator('.symbol-card[data-symbol="GOOGL"]').click();

        await page.waitForSelector('.levels-table');

        // Check table headers
        const table = page.locator('.levels-table');
        await expect(table.locator('thead')).toContainText('Price');
        await expect(table.locator('thead')).toContainText('Type');
        await expect(table.locator('thead')).toContainText('Direction');
        await expect(table.locator('thead')).toContainText('Source');
        await expect(table.locator('thead')).toContainText('Context');
        await expect(table.locator('thead')).toContainText('Confidence');

        // Check we have 5 levels
        const rows = table.locator('tbody tr');
        await expect(rows).toHaveCount(5);

        // Levels should be sorted by price descending
        const firstRow = rows.first();
        await expect(firstRow).toContainText('328'); // Highest price first
    });

    test('should display level type badges with correct styling', async ({ page }) => {
        await page.locator('button[data-tab="symbols"]').click();
        await page.waitForSelector('.symbols-grid');
        await page.locator('.symbol-card[data-symbol="GOOGL"]').click();

        await page.waitForSelector('.levels-table');

        // Check support level badge
        const supportRow = page.locator('.levels-table tbody tr').filter({ hasText: '319' });
        const supportBadge = supportRow.locator('.level-type-support');
        await expect(supportBadge).toBeVisible();
        await expect(supportBadge).toContainText('support');

        // Check target level badge
        const targetRow = page.locator('.levels-table tbody tr').filter({ hasText: '328' });
        const targetBadge = targetRow.locator('.level-type-target');
        await expect(targetBadge).toBeVisible();
        await expect(targetBadge).toContainText('target');

        // Check invalidation level badge
        const invalidationRow = page.locator('.levels-table tbody tr').filter({ hasText: '270' });
        const invalidationBadge = invalidationRow.locator('.level-type-invalidation');
        await expect(invalidationBadge).toBeVisible();
        await expect(invalidationBadge).toContainText('invalidation');
    });

    test('should display fib level labels', async ({ page }) => {
        await page.locator('button[data-tab="symbols"]').click();
        await page.waitForSelector('.symbols-grid');
        await page.locator('.symbol-card[data-symbol="GOOGL"]').click();

        await page.waitForSelector('.levels-table');

        // Check 0.236 fib label on 319 level
        const supportRow = page.locator('.levels-table tbody tr').filter({ hasText: '319' });
        const fibLabel = supportRow.locator('.fib-label');
        await expect(fibLabel).toBeVisible();
        await expect(fibLabel).toContainText('0.236');
    });

    test('should display confluence analysis section', async ({ page }) => {
        await page.locator('button[data-tab="symbols"]').click();
        await page.waitForSelector('.symbols-grid');
        await page.locator('.symbol-card[data-symbol="GOOGL"]').click();

        await page.waitForSelector('.confluence-section');

        const confluenceSection = page.locator('.confluence-section');
        await expect(confluenceSection).toContainText('Confluence Analysis');
        await expect(confluenceSection).toContainText('Score: 85% ✅ Aligned');
        await expect(confluenceSection).toContainText('Both KT Technical and Discord Options indicate bullish bias');
    });

    test('should display trade setup suggestion', async ({ page }) => {
        await page.locator('button[data-tab="symbols"]').click();
        await page.waitForSelector('.symbols-grid');
        await page.locator('.symbol-card[data-symbol="GOOGL"]').click();

        await page.waitForSelector('.trade-setup');

        const tradeSetup = page.locator('.trade-setup');
        await expect(tradeSetup).toBeVisible();
        await expect(tradeSetup).toContainText('Suggested Setup');
        await expect(tradeSetup).toContainText('Consider call spreads targeting 328 with stops below 310');
    });

    test('should close modal on close button click', async ({ page }) => {
        await page.locator('button[data-tab="symbols"]').click();
        await page.waitForSelector('.symbols-grid');
        await page.locator('.symbol-card[data-symbol="GOOGL"]').click();

        // Wait for modal to open
        await page.waitForSelector('#symbol-detail-modal.active');

        // Click close button
        await page.locator('#close-symbol-detail').click();

        // Modal should be hidden
        const modal = page.locator('#symbol-detail-modal');
        await expect(modal).not.toHaveClass(/active/);
    });

    test('should close modal on backdrop click', async ({ page }) => {
        await page.locator('button[data-tab="symbols"]').click();
        await page.waitForSelector('.symbols-grid');
        await page.locator('.symbol-card[data-symbol="GOOGL"]').click();

        await page.waitForSelector('#symbol-detail-modal.active');

        // Click on modal backdrop (not the content)
        await page.locator('#symbol-detail-modal').click({ position: { x: 10, y: 10 } });

        // Modal should be hidden
        const modal = page.locator('#symbol-detail-modal');
        await expect(modal).not.toHaveClass(/active/);
    });

    test('should display empty state when no symbols', async ({ page }) => {
        // Override mock to return empty symbols
        await page.route('**/api/symbols', async route => {
            await route.fulfill({ json: { symbols: [] } });
        });

        await page.goto('http://localhost:8000');
        await page.locator('button[data-tab="symbols"]').click();

        await page.waitForSelector('.empty-state');

        const emptyState = page.locator('.empty-state');
        await expect(emptyState).toBeVisible();
        await expect(emptyState).toContainText('No symbol data available yet');
        await expect(emptyState).toContainText('Run data collection to populate symbol analysis');
    });

    test('should display confidence warnings for low confidence levels', async ({ page }) => {
        await page.locator('button[data-tab="symbols"]').click();
        await page.waitForSelector('.symbols-grid');
        await page.locator('.symbol-card[data-symbol="GOOGL"]').click();

        await page.waitForSelector('.levels-table');

        // The 0.5 fib level at 308 has confidence 0.75 (should show warning)
        const lowConfRow = page.locator('.levels-table tbody tr').filter({ hasText: '308' });
        await expect(lowConfRow).toHaveAttribute('data-low-confidence', 'true');
    });

    test('should handle API errors gracefully', async ({ page }) => {
        // Override mock to return error
        await page.route('**/api/symbols', async route => {
            await route.fulfill({ status: 500, json: { detail: 'Internal server error' } });
        });

        await page.goto('http://localhost:8000');
        await page.locator('button[data-tab="symbols"]').click();

        // Should display error message
        const errorAlert = page.locator('.alert-error');
        await expect(errorAlert).toBeVisible();
        await expect(errorAlert).toContainText('Failed to load symbols');
    });
});

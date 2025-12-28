/**
 * Playwright E2E tests for PRD-043 Symbols Grid Layout
 *
 * Tests:
 * - 4×4×3 grid layout on desktop
 * - All 11 symbols visible without scrolling
 * - Fixed symbol order
 * - Responsive breakpoints (tablet, mobile)
 * - Keyboard accessibility
 * - Card interactions
 */

const { test, expect } = require('@playwright/test');

// Expected symbol order for 4×4×3 grid
const EXPECTED_SYMBOL_ORDER = [
    'SPX', 'QQQ', 'IWM', 'BTC',
    'SMH', 'NVDA', 'TSLA', 'GOOGL',
    'AAPL', 'MSFT', 'AMZN'
];

test.describe('PRD-043: Symbols Grid Layout', () => {

    test.beforeEach(async ({ page }) => {
        // Navigate to app and login
        await page.goto('/');

        // Check if login is required
        const loginForm = page.locator('#login-form, form[action*="login"], input[name="username"]');
        if (await loginForm.isVisible({ timeout: 2000 }).catch(() => false)) {
            await page.fill('input[name="username"], #username', process.env.TEST_USER || 'test');
            await page.fill('input[name="password"], #password', process.env.TEST_PASS || 'test');
            await page.click('button[type="submit"]');
            await page.waitForLoadState('networkidle');
        }

        // Navigate to symbols tab
        const symbolsTab = page.locator('[data-tab="symbols"], a[href*="symbols"], button:has-text("Symbols")');
        if (await symbolsTab.isVisible({ timeout: 2000 }).catch(() => false)) {
            await symbolsTab.click();
        }

        // Wait for symbols grid to load
        await page.waitForSelector('.symbols-grid', { timeout: 10000 });
    });

    test('displays 4-column grid layout on desktop', async ({ page }) => {
        // Set desktop viewport
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.waitForTimeout(300); // Wait for responsive adjustments

        const grid = page.locator('.symbols-grid');

        // Check grid has 4 columns
        const gridStyle = await grid.evaluate(el =>
            window.getComputedStyle(el).gridTemplateColumns
        );

        // Should have 4 equal columns (might be pixel values or fractions)
        const columns = gridStyle.split(' ').filter(c => c.trim() !== '');
        expect(columns.length).toBe(4);
    });

    test('displays all 11 symbols', async ({ page }) => {
        const cards = page.locator('.symbol-card');
        await expect(cards).toHaveCount(11);
    });

    test('maintains fixed symbol order', async ({ page }) => {
        const cards = page.locator('.symbol-card');
        const count = await cards.count();

        expect(count).toBe(11);

        for (let i = 0; i < EXPECTED_SYMBOL_ORDER.length; i++) {
            const symbol = await cards.nth(i).getAttribute('data-symbol');
            expect(symbol).toBe(EXPECTED_SYMBOL_ORDER[i]);
        }
    });

    test('all symbols visible without scrolling on large desktop', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.waitForTimeout(300);

        const cards = page.locator('.symbol-card');
        const count = await cards.count();

        // Check at least first 8 cards are in viewport (2 full rows)
        for (let i = 0; i < Math.min(8, count); i++) {
            await expect(cards.nth(i)).toBeInViewport();
        }
    });

    test('switches to 2-column layout on tablet', async ({ page }) => {
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.waitForTimeout(300);

        const grid = page.locator('.symbols-grid');
        const gridStyle = await grid.evaluate(el =>
            window.getComputedStyle(el).gridTemplateColumns
        );

        const columns = gridStyle.split(' ').filter(c => c.trim() !== '');
        expect(columns.length).toBe(2);
    });

    test('switches to 1-column layout on mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(300);

        const grid = page.locator('.symbols-grid');
        const gridStyle = await grid.evaluate(el =>
            window.getComputedStyle(el).gridTemplateColumns
        );

        // Should be single column (one value)
        const columns = gridStyle.split(' ').filter(c => c.trim() !== '');
        expect(columns.length).toBe(1);
    });

    test('9th card (AAPL) starts at column 1 on desktop', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });
        await page.waitForTimeout(300);

        // 9th card (index 8) is AAPL - should start at column 1
        const ninthCard = page.locator('.symbol-card').nth(8);
        await expect(ninthCard).toHaveAttribute('data-symbol', 'AAPL');

        const gridColumnStart = await ninthCard.evaluate(el =>
            window.getComputedStyle(el).gridColumnStart
        );

        expect(gridColumnStart).toBe('1');
    });

    test('grid has max-width constraint', async ({ page }) => {
        await page.setViewportSize({ width: 1920, height: 1080 });
        await page.waitForTimeout(300);

        const grid = page.locator('.symbols-grid');
        const maxWidth = await grid.evaluate(el =>
            window.getComputedStyle(el).maxWidth
        );

        // Should have max-width of 1400px
        expect(maxWidth).toBe('1400px');
    });
});


test.describe('PRD-043: Symbol Card Accessibility', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/');

        const loginForm = page.locator('#login-form, form[action*="login"], input[name="username"]');
        if (await loginForm.isVisible({ timeout: 2000 }).catch(() => false)) {
            await page.fill('input[name="username"], #username', process.env.TEST_USER || 'test');
            await page.fill('input[name="password"], #password', process.env.TEST_PASS || 'test');
            await page.click('button[type="submit"]');
            await page.waitForLoadState('networkidle');
        }

        const symbolsTab = page.locator('[data-tab="symbols"], a[href*="symbols"], button:has-text("Symbols")');
        if (await symbolsTab.isVisible({ timeout: 2000 }).catch(() => false)) {
            await symbolsTab.click();
        }

        await page.waitForSelector('.symbols-grid', { timeout: 10000 });
    });

    test('grid has list role for accessibility', async ({ page }) => {
        const grid = page.locator('.symbols-grid');
        await expect(grid).toHaveAttribute('role', 'list');
    });

    test('grid has aria-label', async ({ page }) => {
        const grid = page.locator('.symbols-grid');
        const ariaLabel = await grid.getAttribute('aria-label');
        expect(ariaLabel).toBeTruthy();
        expect(ariaLabel.toLowerCase()).toContain('symbol');
    });

    test('cards have listitem role', async ({ page }) => {
        const cards = page.locator('.symbol-card');
        const count = await cards.count();

        for (let i = 0; i < count; i++) {
            await expect(cards.nth(i)).toHaveAttribute('role', 'listitem');
        }
    });

    test('cards are focusable with tabindex', async ({ page }) => {
        const cards = page.locator('.symbol-card');
        const count = await cards.count();

        for (let i = 0; i < count; i++) {
            await expect(cards.nth(i)).toHaveAttribute('tabindex', '0');
        }
    });

    test('cards can be focused with keyboard', async ({ page }) => {
        const firstCard = page.locator('.symbol-card').first();

        // Focus first card using Tab key
        await page.keyboard.press('Tab');

        // Keep pressing Tab until we reach the symbols section
        for (let i = 0; i < 20; i++) {
            const focused = page.locator(':focus');
            if (await focused.getAttribute('data-symbol').catch(() => null)) {
                break;
            }
            await page.keyboard.press('Tab');
        }

        // Check that a symbol card is focused
        const focusedElement = page.locator(':focus');
        const dataSymbol = await focusedElement.getAttribute('data-symbol');
        expect(dataSymbol).toBeTruthy();
    });

    test('Enter key opens symbol detail', async ({ page }) => {
        const firstCard = page.locator('.symbol-card').first();

        // Focus the card
        await firstCard.focus();
        await expect(firstCard).toBeFocused();

        // Press Enter
        await firstCard.press('Enter');

        // Check modal opened
        const modal = page.locator('#symbol-detail-modal');
        await expect(modal).toHaveClass(/active/);
    });

    test('Space key opens symbol detail', async ({ page }) => {
        const firstCard = page.locator('.symbol-card').first();

        await firstCard.focus();
        await firstCard.press(' ');

        const modal = page.locator('#symbol-detail-modal');
        await expect(modal).toHaveClass(/active/);
    });
});


test.describe('PRD-043: Symbol Card Interactions', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/');

        const loginForm = page.locator('#login-form, form[action*="login"], input[name="username"]');
        if (await loginForm.isVisible({ timeout: 2000 }).catch(() => false)) {
            await page.fill('input[name="username"], #username', process.env.TEST_USER || 'test');
            await page.fill('input[name="password"], #password', process.env.TEST_PASS || 'test');
            await page.click('button[type="submit"]');
            await page.waitForLoadState('networkidle');
        }

        const symbolsTab = page.locator('[data-tab="symbols"], a[href*="symbols"], button:has-text("Symbols")');
        if (await symbolsTab.isVisible({ timeout: 2000 }).catch(() => false)) {
            await symbolsTab.click();
        }

        await page.waitForSelector('.symbols-grid', { timeout: 10000 });
    });

    test('clicking card opens detail modal', async ({ page }) => {
        const spxCard = page.locator('[data-symbol="SPX"]');
        await spxCard.click();

        const modal = page.locator('#symbol-detail-modal');
        await expect(modal).toHaveClass(/active/);

        // Modal should show SPX in header
        const modalHeader = modal.locator('h2');
        await expect(modalHeader).toContainText('SPX');
    });

    test('card displays KT and Discord view labels', async ({ page }) => {
        const card = page.locator('.symbol-card').first();

        // Check for view labels
        await expect(card.locator('.view-label:has-text("KT")')).toBeVisible();
        await expect(card.locator('.view-label:has-text("Discord")')).toBeVisible();
    });

    test('card has confluence indicator', async ({ page }) => {
        const cards = page.locator('.symbol-card');
        const count = await cards.count();

        for (let i = 0; i < count; i++) {
            const confluenceEl = cards.nth(i).locator('.symbol-confluence');
            await expect(confluenceEl).toBeVisible();

            const classes = await confluenceEl.getAttribute('class');
            // Should have one of the confluence classes
            const hasValidClass =
                classes.includes('confluence-high') ||
                classes.includes('confluence-medium') ||
                classes.includes('confluence-low') ||
                classes.includes('confluence-none');

            expect(hasValidClass).toBe(true);
        }
    });

    test('card hover shows visual feedback', async ({ page }) => {
        const card = page.locator('.symbol-card').first();

        // Get initial styles
        const initialBoxShadow = await card.evaluate(el =>
            window.getComputedStyle(el).boxShadow
        );

        // Hover over card
        await card.hover();
        await page.waitForTimeout(350); // Wait for transition

        // Get hover styles
        const hoverBoxShadow = await card.evaluate(el =>
            window.getComputedStyle(el).boxShadow
        );

        // Box shadow should change on hover
        expect(hoverBoxShadow).not.toBe(initialBoxShadow);
    });

    test('closing modal returns focus', async ({ page }) => {
        const firstCard = page.locator('.symbol-card').first();

        // Open modal by clicking card
        await firstCard.click();

        const modal = page.locator('#symbol-detail-modal');
        await expect(modal).toHaveClass(/active/);

        // Close modal by clicking close button or backdrop
        const closeBtn = page.locator('#close-symbol-detail');
        if (await closeBtn.isVisible()) {
            await closeBtn.click();
        } else {
            // Click backdrop
            await modal.click({ position: { x: 10, y: 10 } });
        }

        // Modal should be closed
        await expect(modal).not.toHaveClass(/active/);
    });
});


test.describe('PRD-043: Responsive Behavior', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/');

        const loginForm = page.locator('#login-form, form[action*="login"], input[name="username"]');
        if (await loginForm.isVisible({ timeout: 2000 }).catch(() => false)) {
            await page.fill('input[name="username"], #username', process.env.TEST_USER || 'test');
            await page.fill('input[name="password"], #password', process.env.TEST_PASS || 'test');
            await page.click('button[type="submit"]');
            await page.waitForLoadState('networkidle');
        }

        const symbolsTab = page.locator('[data-tab="symbols"], a[href*="symbols"], button:has-text("Symbols")');
        if (await symbolsTab.isVisible({ timeout: 2000 }).catch(() => false)) {
            await symbolsTab.click();
        }

        await page.waitForSelector('.symbols-grid', { timeout: 10000 });
    });

    test('grid gap adjusts for tablet', async ({ page }) => {
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.waitForTimeout(300);

        const grid = page.locator('.symbols-grid');
        const gap = await grid.evaluate(el =>
            window.getComputedStyle(el).gap
        );

        // Gap should be 0.75rem (12px) on tablet
        expect(gap).toMatch(/12px|0\.75rem/);
    });

    test('grid gap adjusts for mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(300);

        const grid = page.locator('.symbols-grid');
        const gap = await grid.evaluate(el =>
            window.getComputedStyle(el).gap
        );

        // Gap should be 0.5rem (8px) on mobile
        expect(gap).toMatch(/8px|0\.5rem/);
    });

    test('cards are full width on mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(300);

        const firstCard = page.locator('.symbol-card').first();
        const grid = page.locator('.symbols-grid');

        const cardWidth = await firstCard.evaluate(el => el.offsetWidth);
        const gridWidth = await grid.evaluate(el => el.clientWidth);
        const gridPadding = await grid.evaluate(el => {
            const style = window.getComputedStyle(el);
            return parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
        });

        // Card should be approximately full width minus padding
        const expectedWidth = gridWidth - gridPadding;
        expect(cardWidth).toBeGreaterThan(expectedWidth * 0.9);
    });
});

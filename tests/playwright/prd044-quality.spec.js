/**
 * Playwright UI Tests for PRD-044 Synthesis Quality Widget
 *
 * Tests the quality widget UI interactions:
 * - Quality widget presence and rendering
 * - Grade display with correct colors
 * - Criterion bar visualization
 * - Details expansion/collapse
 * - Flags and suggestions display
 */

const { test, expect } = require('@playwright/test');

// Mock API responses
const mockQualityResponse = {
    synthesis_id: 1,
    quality_score: 78,
    grade: "B+",
    criterion_scores: {
        confluence_detection: 3,
        evidence_preservation: 2,
        source_attribution: 3,
        youtube_channel_granularity: 2,
        nuance_retention: 2,
        actionability: 2,
        theme_continuity: 1
    },
    flags: [
        {
            criterion: "Theme Continuity",
            score: 1,
            detail: "No historical context for themes"
        }
    ],
    prompt_suggestions: [
        "Add references to how themes have evolved from previous syntheses"
    ],
    created_at: new Date().toISOString()
};

const mockHighQualityResponse = {
    synthesis_id: 2,
    quality_score: 95,
    grade: "A+",
    criterion_scores: {
        confluence_detection: 3,
        evidence_preservation: 3,
        source_attribution: 3,
        youtube_channel_granularity: 3,
        nuance_retention: 3,
        actionability: 3,
        theme_continuity: 2
    },
    flags: [],
    prompt_suggestions: [],
    created_at: new Date().toISOString()
};

const mockLowQualityResponse = {
    synthesis_id: 3,
    quality_score: 45,
    grade: "F",
    criterion_scores: {
        confluence_detection: 1,
        evidence_preservation: 1,
        source_attribution: 1,
        youtube_channel_granularity: 0,
        nuance_retention: 1,
        actionability: 1,
        theme_continuity: 0
    },
    flags: [
        {
            criterion: "YouTube Channel Granularity",
            score: 0,
            detail: "YouTube mentioned generically with no channel names"
        },
        {
            criterion: "Theme Continuity",
            score: 0,
            detail: "No theme evolution tracking"
        },
        {
            criterion: "Confluence Detection",
            score: 1,
            detail: "Cross-source alignments not explicitly identified"
        }
    ],
    prompt_suggestions: [
        "Name YouTube channels individually (e.g., Moonshots, Forward Guidance)",
        "Reference how themes evolved from previous syntheses",
        "Explicitly note when multiple sources agree"
    ],
    created_at: new Date().toISOString()
};

const mockTrendsResponse = {
    period_days: 30,
    total_evaluations: 15,
    average_score: 72,
    min_score: 45,
    max_score: 95,
    grade_distribution: {
        "A+": 1,
        "A": 2,
        "B+": 5,
        "B": 4,
        "C+": 2,
        "F": 1
    },
    criterion_averages: {
        confluence_detection: 2.5,
        evidence_preservation: 2.2,
        source_attribution: 2.4,
        youtube_channel_granularity: 1.8,
        nuance_retention: 2.1,
        actionability: 2.0,
        theme_continuity: 1.5
    },
    weakest_criterion: "theme_continuity",
    strongest_criterion: "confluence_detection",
    trend: "improving",
    trend_delta: 3.5
};

test.describe('PRD-044 Quality Widget', () => {

    test.describe('Widget Rendering', () => {

        test('quality widget renders with valid data', async ({ page }) => {
            // Mock APIs
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockQualityResponse)
                });
            });

            await page.route('**/api/synthesis/latest**', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({ id: 1, synthesis: "test" })
                });
            });

            await page.goto('/');

            // Trigger quality load by dispatching synthesisLoaded event
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            // Wait for quality widget
            await page.waitForSelector('#quality-widget', { timeout: 5000 });

            const widget = page.locator('#quality-widget');
            await expect(widget).toBeVisible();
        });

        test('displays correct grade', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('.quality-grade', { timeout: 5000 });

            const grade = page.locator('.quality-grade');
            await expect(grade).toContainText('B+');
        });

        test('displays correct score', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('.quality-score', { timeout: 5000 });

            const score = page.locator('.quality-score');
            await expect(score).toContainText('78/100');
        });

    });

    test.describe('Grade Colors', () => {

        test('A+ grade shows success color class', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockHighQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('.quality-grade', { timeout: 5000 });

            const grade = page.locator('.quality-grade');
            await expect(grade).toHaveClass(/grade-a/);
        });

        test('F grade shows error color class', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockLowQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('.quality-grade', { timeout: 5000 });

            const grade = page.locator('.quality-grade');
            await expect(grade).toHaveClass(/grade-f/);
        });

        test('B+ grade shows info color class', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('.quality-grade', { timeout: 5000 });

            const grade = page.locator('.quality-grade');
            await expect(grade).toHaveClass(/grade-b/);
        });

    });

    test.describe('Criterion Bars', () => {

        test('renders all 7 criterion bars', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('.criterion-row', { timeout: 5000 });

            const rows = page.locator('.criterion-row');
            await expect(rows).toHaveCount(7);
        });

        test('criterion bars have correct labels', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('#quality-criteria', { timeout: 5000 });

            const criteria = page.locator('#quality-criteria');
            await expect(criteria).toContainText('Confluence');
            await expect(criteria).toContainText('Evidence');
            await expect(criteria).toContainText('Attribution');
            await expect(criteria).toContainText('YT Channels');
            await expect(criteria).toContainText('Nuance');
            await expect(criteria).toContainText('Actionable');
            await expect(criteria).toContainText('Continuity');
        });

        test('criterion bars show score values', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('.criterion-score', { timeout: 5000 });

            const scores = page.locator('.criterion-score');
            await expect(scores.first()).toContainText('/3');
        });

    });

    test.describe('Flags Display', () => {

        test('shows flags indicator when issues exist', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('.quality-flags-warning', { timeout: 5000 });

            const flagsIndicator = page.locator('.quality-flags-warning');
            await expect(flagsIndicator).toContainText('1 issue');
        });

        test('shows "No issues" when no flags', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockHighQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('.quality-flags-ok', { timeout: 5000 });

            const flagsOk = page.locator('.quality-flags-ok');
            await expect(flagsOk).toContainText('No issues');
        });

        test('shows multiple issues count', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockLowQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('.quality-flags-warning', { timeout: 5000 });

            const flagsIndicator = page.locator('.quality-flags-warning');
            await expect(flagsIndicator).toContainText('3 issues');
        });

    });

    test.describe('Details Expansion', () => {

        test('expand button exists', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('#quality-expand-btn', { timeout: 5000 });

            const expandBtn = page.locator('#quality-expand-btn');
            await expect(expandBtn).toBeVisible();
        });

        test('details hidden by default', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('#quality-details', { timeout: 5000 });

            const details = page.locator('#quality-details');
            await expect(details).toBeHidden();
        });

        test('clicking expand button shows details', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('#quality-expand-btn', { timeout: 5000 });

            // Click expand
            await page.click('#quality-expand-btn');

            // Details should be visible
            const details = page.locator('#quality-details');
            await expect(details).toBeVisible();
        });

        test('expanded details show flags', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('#quality-expand-btn', { timeout: 5000 });
            await page.click('#quality-expand-btn');

            await page.waitForSelector('.quality-flag-item', { timeout: 2000 });

            const flagItem = page.locator('.quality-flag-item');
            await expect(flagItem).toContainText('Theme Continuity');
        });

        test('expanded details show suggestions', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('#quality-expand-btn', { timeout: 5000 });
            await page.click('#quality-expand-btn');

            await page.waitForSelector('.quality-suggestion-item', { timeout: 2000 });

            const suggestionItem = page.locator('.quality-suggestion-item');
            await expect(suggestionItem).toContainText('evolved');
        });

        test('clicking expand again collapses details', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('#quality-expand-btn', { timeout: 5000 });

            // Expand
            await page.click('#quality-expand-btn');
            await page.waitForSelector('#quality-details:visible', { timeout: 2000 });

            // Collapse
            await page.click('#quality-expand-btn');

            const details = page.locator('#quality-details');
            await expect(details).toBeHidden();
        });

    });

    test.describe('Error Handling', () => {

        test('hides widget when no quality data', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({ status: 'not_found', message: 'No quality data' })
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            // Widget should be hidden or not exist
            await page.waitForTimeout(1000);

            const widget = page.locator('#quality-widget');
            const isHidden = await widget.isHidden().catch(() => true);
            expect(isHidden).toBe(true);
        });

        test('hides widget on API error', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 500,
                    contentType: 'application/json',
                    body: JSON.stringify({ error: 'Server error' })
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForTimeout(1000);

            const widget = page.locator('#quality-widget');
            const isHidden = await widget.isHidden().catch(() => true);
            expect(isHidden).toBe(true);
        });

    });

    test.describe('Accessibility', () => {

        test('expand button has title attribute', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('#quality-expand-btn', { timeout: 5000 });

            const expandBtn = page.locator('#quality-expand-btn');
            await expect(expandBtn).toHaveAttribute('title', /detail/i);
        });

        test('criterion weights are displayed', async ({ page }) => {
            await page.route('**/api/quality/latest', route => {
                route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockQualityResponse)
                });
            });

            await page.goto('/');
            await page.evaluate(() => {
                document.dispatchEvent(new Event('synthesisLoaded'));
            });

            await page.waitForSelector('.criterion-weight', { timeout: 5000 });

            const weights = page.locator('.criterion-weight');
            const firstWeight = weights.first();
            await expect(firstWeight).toContainText('%');
        });

    });

});

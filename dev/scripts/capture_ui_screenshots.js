/**
 * Playwright script to capture screenshots of the current dashboard UI
 * For UI/UX analysis and modernization planning
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const DASHBOARD_URL = 'https://confluence-production-a32e.up.railway.app/index.html';
const AUTH = {
    username: 'sames3',
    password: 'Spotswood1'
};

const SCREENSHOTS_DIR = path.join(__dirname, '../../design/current-ui');

async function captureScreenshots() {
    // Ensure screenshots directory exists
    if (!fs.existsSync(SCREENSHOTS_DIR)) {
        fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
    }

    console.log('Launching browser...');
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        httpCredentials: AUTH,
        viewport: { width: 1920, height: 1080 }
    });

    const page = await context.newPage();

    try {
        console.log('Navigating to dashboard...');
        await page.goto(DASHBOARD_URL, { waitUntil: 'networkidle', timeout: 60000 });

        // Wait for content to load
        await page.waitForTimeout(3000);

        // 1. Full page screenshot - Desktop
        console.log('Capturing desktop full page...');
        await page.screenshot({
            path: path.join(SCREENSHOTS_DIR, '01-desktop-full-page.png'),
            fullPage: true
        });

        // 2. Above the fold - Desktop
        console.log('Capturing desktop above the fold...');
        await page.screenshot({
            path: path.join(SCREENSHOTS_DIR, '02-desktop-above-fold.png'),
            fullPage: false
        });

        // 3. Synthesis panel close-up
        console.log('Capturing synthesis panel...');
        const synthesisPanel = await page.$('.synthesis-panel');
        if (synthesisPanel) {
            await synthesisPanel.screenshot({
                path: path.join(SCREENSHOTS_DIR, '03-synthesis-panel.png')
            });
        }

        // 4. Status cards section
        console.log('Capturing status cards...');
        const statusGrid = await page.$('.status-grid');
        if (statusGrid) {
            await statusGrid.screenshot({
                path: path.join(SCREENSHOTS_DIR, '04-status-cards.png')
            });
        }

        // 5. Switch to Themes tab if it exists
        console.log('Looking for Themes tab...');
        const themesTab = await page.$('text=Themes');
        if (themesTab) {
            await themesTab.click();
            await page.waitForTimeout(1500);

            console.log('Capturing themes tab...');
            await page.screenshot({
                path: path.join(SCREENSHOTS_DIR, '05-themes-tab.png'),
                fullPage: true
            });
        }

        // 6. Mobile viewport
        console.log('Capturing mobile view...');
        await page.setViewportSize({ width: 375, height: 812 });

        // Go back to main tab
        const synthesisTab = await page.$('text=Research Synthesis');
        if (synthesisTab) {
            await synthesisTab.click();
            await page.waitForTimeout(1000);
        }

        await page.screenshot({
            path: path.join(SCREENSHOTS_DIR, '06-mobile-view.png'),
            fullPage: true
        });

        // 7. Tablet viewport
        console.log('Capturing tablet view...');
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.screenshot({
            path: path.join(SCREENSHOTS_DIR, '07-tablet-view.png'),
            fullPage: true
        });

        console.log('\nScreenshots saved to:', SCREENSHOTS_DIR);
        console.log('Files created:');
        const files = fs.readdirSync(SCREENSHOTS_DIR);
        files.forEach(f => console.log('  -', f));

    } catch (error) {
        console.error('Error capturing screenshots:', error.message);
    } finally {
        await browser.close();
    }
}

captureScreenshots();

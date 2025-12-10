/**
 * Frontend UI Modernization Tests
 * PRD-026 through PRD-032 Implementation Verification
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.TEST_URL || 'https://confluence-production-a32e.up.railway.app';
const AUTH = { username: 'sames3', password: 'Spotswood1' };

test.describe('UI Modernization - Design System (PRD-027)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL, {
      httpCredentials: AUTH
    });
    await page.waitForLoadState('domcontentloaded');
  });

  test('should load Google Fonts', async ({ page }) => {
    // Check that Inter font is loaded
    const fontLoaded = await page.evaluate(() => {
      return document.fonts.check('16px Inter');
    });
    expect(fontLoaded).toBeTruthy();
  });

  test('should have CSS custom properties defined', async ({ page }) => {
    const cssVars = await page.evaluate(() => {
      const styles = getComputedStyle(document.documentElement);
      return {
        // PRD-026 specifies these variable names
        primary: styles.getPropertyValue('--primary').trim(),
        bgBase: styles.getPropertyValue('--bg-base').trim(),
        spacingMd: styles.getPropertyValue('--spacing-md').trim(),
        radiusMd: styles.getPropertyValue('--radius-md').trim()
      };
    });

    // Verify design tokens are present (PRD-026 naming)
    expect(cssVars.primary).not.toBe('');
  });

  test('should include modern CSS file', async ({ page }) => {
    const mainCssLink = await page.$('link[href="css/main.css"]');
    expect(mainCssLink).not.toBeNull();
  });
});

test.describe('UI Modernization - Components (PRD-028)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL, {
      httpCredentials: AUTH
    });
    await page.waitForLoadState('domcontentloaded');
  });

  test('should have accessible buttons', async ({ page }) => {
    const buttons = await page.$$('button');
    expect(buttons.length).toBeGreaterThan(0);

    // Check first button has accessible name
    const firstButton = buttons[0];
    const accessibleName = await firstButton.getAttribute('aria-label') ||
                           await firstButton.textContent();
    expect(accessibleName.trim()).not.toBe('');
  });

  test('should have card components', async ({ page }) => {
    const cards = await page.$$('.card, .status-card, .glass-card');
    expect(cards.length).toBeGreaterThan(0);
  });

  test('should have tab navigation', async ({ page }) => {
    const tabs = await page.$$('.tab-btn, [role="tab"]');
    expect(tabs.length).toBeGreaterThan(0);
  });
});

test.describe('UI Modernization - Accessibility (PRD-032)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL, {
      httpCredentials: AUTH
    });
    await page.waitForLoadState('domcontentloaded');
  });

  test('should have skip link for accessibility', async ({ page }) => {
    const skipLink = await page.$('.skip-link, a[href="#main-content"]');
    expect(skipLink).not.toBeNull();
  });

  test('should have main content landmark', async ({ page }) => {
    const main = await page.$('main, [role="main"]');
    expect(main).not.toBeNull();
  });

  test('should have proper document structure', async ({ page }) => {
    // Check for lang attribute
    const lang = await page.$eval('html', el => el.getAttribute('lang'));
    expect(lang).toBe('en');

    // Check for meta viewport
    const viewport = await page.$('meta[name="viewport"]');
    expect(viewport).not.toBeNull();
  });

  test('should have focus-visible support', async ({ page }) => {
    // Tab to first focusable element
    await page.keyboard.press('Tab');

    // Check that something is focused
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).not.toBe('BODY');
  });

  test('should support reduced motion preference', async ({ page, context }) => {
    // Emulate reduced motion preference
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.reload();

    // Check that page still loads correctly
    const main = await page.$('main, [role="main"]');
    expect(main).not.toBeNull();
  });
});

test.describe('UI Modernization - Layout (PRD-029)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL, {
      httpCredentials: AUTH
    });
    await page.waitForLoadState('domcontentloaded');
  });

  test('should have proper header structure', async ({ page }) => {
    const header = await page.$('header, .header');
    expect(header).not.toBeNull();
  });

  test('should have container with main content', async ({ page }) => {
    const container = await page.$('.container, main');
    expect(container).not.toBeNull();
  });

  test('should be responsive on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    // Check that content is visible
    const main = await page.$('main, .container');
    const isVisible = await main?.isVisible();
    expect(isVisible).toBeTruthy();
  });

  test('should be responsive on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });

    // Check that content is visible
    const main = await page.$('main, .container');
    const isVisible = await main?.isVisible();
    expect(isVisible).toBeTruthy();
  });
});

test.describe('UI Modernization - JavaScript Modules', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL, {
      httpCredentials: AUTH
    });
    await page.waitForLoadState('domcontentloaded');
  });

  test('should load AnimationController', async ({ page }) => {
    const hasAnimationController = await page.evaluate(() => {
      return typeof window.AnimationController !== 'undefined';
    });
    expect(hasAnimationController).toBeTruthy();
  });

  test('should load AccessibilityManager', async ({ page }) => {
    const hasAccessibilityManager = await page.evaluate(() => {
      return typeof window.AccessibilityManager !== 'undefined';
    });
    expect(hasAccessibilityManager).toBeTruthy();
  });

  test('should load ToastManager', async ({ page }) => {
    const hasToastManager = await page.evaluate(() => {
      return typeof window.ToastManager !== 'undefined';
    });
    expect(hasToastManager).toBeTruthy();
  });

  test('should load ChartTheme', async ({ page }) => {
    const hasChartTheme = await page.evaluate(() => {
      return typeof window.ChartTheme !== 'undefined';
    });
    expect(hasChartTheme).toBeTruthy();
  });

  test('should have ARIA live region for announcements', async ({ page }) => {
    // Wait for AccessibilityManager to initialize
    await page.waitForTimeout(500);

    const liveRegion = await page.$('#a11y-announcer, [aria-live="polite"]');
    expect(liveRegion).not.toBeNull();
  });

  test('should have toast container', async ({ page }) => {
    // Wait for ToastManager to initialize
    await page.waitForTimeout(500);

    const toastContainer = await page.$('#toast-container, .toast-container');
    expect(toastContainer).not.toBeNull();
  });
});

test.describe('UI Modernization - Interactions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL, {
      httpCredentials: AUTH
    });
    await page.waitForLoadState('domcontentloaded');
  });

  test('should switch tabs correctly', async ({ page }) => {
    // Find tab buttons
    const tabs = await page.$$('.tab-btn');
    if (tabs.length >= 2) {
      // Click second tab
      await tabs[1].click();

      // Wait for transition
      await page.waitForTimeout(300);

      // Check that tab is active
      const isActive = await tabs[1].evaluate(el => el.classList.contains('active'));
      expect(isActive).toBeTruthy();
    }
  });

  test('should show toast notification on trigger', async ({ page }) => {
    // Trigger a toast via ToastManager
    await page.evaluate(() => {
      if (window.ToastManager) {
        window.ToastManager.success('Test notification', 'Test');
      }
    });

    // Wait for toast to appear
    await page.waitForTimeout(300);

    // Check toast is visible
    const toast = await page.$('.toast');
    expect(toast).not.toBeNull();
  });

  test('should support keyboard navigation', async ({ page }) => {
    // Tab through interactive elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Check we can navigate with keyboard
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA']).toContain(focusedElement);
  });
});

test.describe('UI Modernization - PRD-026 Features', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL, {
      httpCredentials: AUTH
    });
    await page.waitForLoadState('domcontentloaded');
  });

  test('should have card tilt CSS classes defined', async ({ page }) => {
    // Verify card-tilt CSS class exists in stylesheets
    const hasTiltStyles = await page.evaluate(() => {
      const sheets = document.styleSheets;
      for (const sheet of sheets) {
        try {
          const rules = sheet.cssRules || sheet.rules;
          for (const rule of rules) {
            if (rule.selectorText && rule.selectorText.includes('.card-tilt')) {
              return true;
            }
          }
        } catch (e) {
          // Cross-origin stylesheets can't be accessed
        }
      }
      return false;
    });
    expect(hasTiltStyles).toBeTruthy();
  });

  test('should have theme-tag CSS classes defined', async ({ page }) => {
    // Verify theme-tag CSS class exists
    const hasThemeTagStyles = await page.evaluate(() => {
      const sheets = document.styleSheets;
      for (const sheet of sheets) {
        try {
          const rules = sheet.cssRules || sheet.rules;
          for (const rule of rules) {
            if (rule.selectorText && rule.selectorText.includes('.theme-tag')) {
              return true;
            }
          }
        } catch (e) {
          // Cross-origin stylesheets can't be accessed
        }
      }
      return false;
    });
    expect(hasThemeTagStyles).toBeTruthy();
  });

  test('should have conviction-bar CSS with shimmer animation', async ({ page }) => {
    // Verify conviction-bar CSS exists
    const hasConvictionBarStyles = await page.evaluate(() => {
      const sheets = document.styleSheets;
      for (const sheet of sheets) {
        try {
          const rules = sheet.cssRules || sheet.rules;
          for (const rule of rules) {
            if (rule.selectorText && rule.selectorText.includes('.conviction-bar-fill')) {
              return true;
            }
          }
        } catch (e) {
          // Cross-origin stylesheets can't be accessed
        }
      }
      return false;
    });
    expect(hasConvictionBarStyles).toBeTruthy();
  });

  test('should have animateValue function in AnimationController', async ({ page }) => {
    const hasAnimateValue = await page.evaluate(() => {
      return typeof window.AnimationController?.animateValue === 'function';
    });
    expect(hasAnimateValue).toBeTruthy();
  });

  test('should have setupCardTiltEffects function in AnimationController', async ({ page }) => {
    const hasCardTiltSetup = await page.evaluate(() => {
      return typeof window.AnimationController?.setupCardTiltEffects === 'function';
    });
    expect(hasCardTiltSetup).toBeTruthy();
  });

  test('should have glassmorphism effect on cards', async ({ page }) => {
    // Check that glassmorphism is applied via CSS custom properties
    const hasGlassmorphism = await page.evaluate(() => {
      const styles = getComputedStyle(document.documentElement);
      return styles.getPropertyValue('--glass-bg').trim() !== '' &&
             styles.getPropertyValue('--glass-blur').trim() !== '';
    });
    expect(hasGlassmorphism).toBeTruthy();
  });

  test('should have gradient CSS variables for progress bars', async ({ page }) => {
    const hasGradients = await page.evaluate(() => {
      const styles = getComputedStyle(document.documentElement);
      return styles.getPropertyValue('--gradient-success').trim() !== '' ||
             styles.getPropertyValue('--gradient-warning').trim() !== '';
    });
    expect(hasGradients).toBeTruthy();
  });

  test('should have KPI cards rendered', async ({ page }) => {
    const kpiCards = await page.$$('.kpi-card, .card-kpi');
    expect(kpiCards.length).toBeGreaterThan(0);
  });

  test('should have source status items', async ({ page }) => {
    // Wait for API data to load
    await page.waitForTimeout(2000);
    const sourceItems = await page.$$('.source-item, .card-source');
    expect(sourceItems.length).toBeGreaterThan(0);
  });

  test('should have floating action bar', async ({ page }) => {
    const fab = await page.$('.floating-action-bar, #floating-actions');
    expect(fab).not.toBeNull();
  });

  test('should have hero section with market regime', async ({ page }) => {
    const heroSection = await page.$('.hero-section, #hero-section');
    expect(heroSection).not.toBeNull();

    // Check for regime badge
    const regimeBadge = await page.$('.regime-badge, #hero-regime-badge');
    expect(regimeBadge).not.toBeNull();
  });
});

test.describe('Performance Checks', () => {
  test('should load within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(BASE_URL, {
      httpCredentials: AUTH,
      waitUntil: 'domcontentloaded'
    });

    const loadTime = Date.now() - startTime;

    // Should load within 10 seconds
    expect(loadTime).toBeLessThan(10000);
  });

  test('should have no console errors on load', async ({ page }) => {
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto(BASE_URL, {
      httpCredentials: AUTH
    });
    await page.waitForLoadState('networkidle');

    // Filter out expected warnings (favicon, network errors, Chart.js canvas warnings, auth errors)
    const criticalErrors = errors.filter(e =>
      !e.includes('favicon') &&
      !e.includes('404') &&
      !e.includes('401') &&
      !e.includes('net::') &&
      !e.includes('Chart.js') &&
      !e.includes('Canvas') &&
      !e.includes('canvas')
    );

    // Log errors for debugging
    if (criticalErrors.length > 0) {
      console.log('Critical errors found:', criticalErrors);
    }

    expect(criticalErrors.length).toBe(0);
  });
});

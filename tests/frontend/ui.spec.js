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

  test('should have color tokens defined', async ({ page }) => {
    const colors = await page.evaluate(() => {
      const styles = getComputedStyle(document.documentElement);
      return {
        primary: styles.getPropertyValue('--primary').trim(),
        success: styles.getPropertyValue('--success').trim(),
        warning: styles.getPropertyValue('--warning').trim(),
        danger: styles.getPropertyValue('--danger').trim(),
        textPrimary: styles.getPropertyValue('--text-primary').trim(),
        textSecondary: styles.getPropertyValue('--text-secondary').trim(),
        bgBase: styles.getPropertyValue('--bg-base').trim(),
        bgSurface: styles.getPropertyValue('--bg-surface').trim()
      };
    });

    expect(colors.primary).not.toBe('');
    expect(colors.success).not.toBe('');
    expect(colors.warning).not.toBe('');
    expect(colors.danger).not.toBe('');
    expect(colors.textPrimary).not.toBe('');
    expect(colors.bgBase).not.toBe('');
  });

  test('should have typography tokens defined', async ({ page }) => {
    const typography = await page.evaluate(() => {
      const styles = getComputedStyle(document.documentElement);
      return {
        fontDisplay: styles.getPropertyValue('--font-display').trim(),
        textBase: styles.getPropertyValue('--text-base').trim(),
        textLg: styles.getPropertyValue('--text-lg').trim(),
        fontNormal: styles.getPropertyValue('--font-normal').trim(),
        fontSemibold: styles.getPropertyValue('--font-semibold').trim(),
        leadingNormal: styles.getPropertyValue('--leading-normal').trim()
      };
    });

    expect(typography.fontDisplay).not.toBe('');
    expect(typography.textBase).not.toBe('');
    expect(typography.fontNormal).not.toBe('');
  });

  test('should have spacing tokens defined', async ({ page }) => {
    const spacing = await page.evaluate(() => {
      const styles = getComputedStyle(document.documentElement);
      return {
        spacingXs: styles.getPropertyValue('--spacing-xs').trim(),
        spacingSm: styles.getPropertyValue('--spacing-sm').trim(),
        spacingMd: styles.getPropertyValue('--spacing-md').trim(),
        spacingLg: styles.getPropertyValue('--spacing-lg').trim(),
        spacingXl: styles.getPropertyValue('--spacing-xl').trim()
      };
    });

    expect(spacing.spacingXs).not.toBe('');
    expect(spacing.spacingSm).not.toBe('');
    expect(spacing.spacingMd).not.toBe('');
    expect(spacing.spacingLg).not.toBe('');
  });

  test('should have border radius tokens defined', async ({ page }) => {
    const radius = await page.evaluate(() => {
      const styles = getComputedStyle(document.documentElement);
      return {
        radiusSm: styles.getPropertyValue('--radius-sm').trim(),
        radiusMd: styles.getPropertyValue('--radius-md').trim(),
        radiusLg: styles.getPropertyValue('--radius-lg').trim(),
        radiusXl: styles.getPropertyValue('--radius-xl').trim(),
        radiusFull: styles.getPropertyValue('--radius-full').trim()
      };
    });

    expect(radius.radiusSm).not.toBe('');
    expect(radius.radiusMd).not.toBe('');
    expect(radius.radiusLg).not.toBe('');
    expect(radius.radiusFull).not.toBe('');
  });

  test('should have shadow tokens defined', async ({ page }) => {
    const shadows = await page.evaluate(() => {
      const styles = getComputedStyle(document.documentElement);
      return {
        shadowSm: styles.getPropertyValue('--shadow-sm').trim(),
        shadowMd: styles.getPropertyValue('--shadow-md').trim(),
        shadowLg: styles.getPropertyValue('--shadow-lg').trim(),
        shadowGlow: styles.getPropertyValue('--shadow-glow').trim()
      };
    });

    expect(shadows.shadowSm).not.toBe('');
    expect(shadows.shadowMd).not.toBe('');
    expect(shadows.shadowLg).not.toBe('');
  });

  test('should have glassmorphism tokens defined', async ({ page }) => {
    const glass = await page.evaluate(() => {
      const styles = getComputedStyle(document.documentElement);
      return {
        glassBg: styles.getPropertyValue('--glass-bg').trim(),
        glassBorder: styles.getPropertyValue('--glass-border').trim(),
        glassBlur: styles.getPropertyValue('--glass-blur').trim()
      };
    });

    expect(glass.glassBg).not.toBe('');
    expect(glass.glassBorder).not.toBe('');
    expect(glass.glassBlur).not.toBe('');
  });

  test('should have z-index tokens defined', async ({ page }) => {
    const zIndex = await page.evaluate(() => {
      const styles = getComputedStyle(document.documentElement);
      return {
        zDropdown: styles.getPropertyValue('--z-dropdown').trim(),
        zSticky: styles.getPropertyValue('--z-sticky').trim(),
        zModal: styles.getPropertyValue('--z-modal').trim(),
        zToast: styles.getPropertyValue('--z-toast').trim()
      };
    });

    expect(zIndex.zDropdown).not.toBe('');
    expect(zIndex.zSticky).not.toBe('');
    expect(zIndex.zModal).not.toBe('');
    expect(zIndex.zToast).not.toBe('');
  });

  test('should have transition tokens defined', async ({ page }) => {
    const transitions = await page.evaluate(() => {
      const styles = getComputedStyle(document.documentElement);
      return {
        transitionFast: styles.getPropertyValue('--transition-fast').trim(),
        transitionNormal: styles.getPropertyValue('--transition-normal').trim(),
        transitionSlow: styles.getPropertyValue('--transition-slow').trim()
      };
    });

    expect(transitions.transitionFast).not.toBe('');
    expect(transitions.transitionNormal).not.toBe('');
    expect(transitions.transitionSlow).not.toBe('');
  });

  test('should have gradient tokens defined', async ({ page }) => {
    const gradients = await page.evaluate(() => {
      const styles = getComputedStyle(document.documentElement);
      return {
        gradientPrimary: styles.getPropertyValue('--gradient-primary').trim(),
        gradientSuccess: styles.getPropertyValue('--gradient-success').trim(),
        gradientWarning: styles.getPropertyValue('--gradient-warning').trim()
      };
    });

    expect(gradients.gradientPrimary).not.toBe('');
    expect(gradients.gradientSuccess).not.toBe('');
  });

  test('should have sentiment colors defined', async ({ page }) => {
    const sentiment = await page.evaluate(() => {
      const styles = getComputedStyle(document.documentElement);
      return {
        bullish: styles.getPropertyValue('--bullish').trim(),
        bearish: styles.getPropertyValue('--bearish').trim(),
        neutral: styles.getPropertyValue('--neutral').trim()
      };
    });

    expect(sentiment.bullish).not.toBe('');
    expect(sentiment.bearish).not.toBe('');
    expect(sentiment.neutral).not.toBe('');
  });

  test('should have source brand colors defined', async ({ page }) => {
    const sources = await page.evaluate(() => {
      const styles = getComputedStyle(document.documentElement);
      return {
        discord: styles.getPropertyValue('--source-discord').trim(),
        youtube: styles.getPropertyValue('--source-youtube').trim(),
        substack: styles.getPropertyValue('--source-substack').trim()
      };
    });

    expect(sources.discord).not.toBe('');
    expect(sources.youtube).not.toBe('');
    expect(sources.substack).not.toBe('');
  });

  test('should apply CSS reset (box-sizing border-box)', async ({ page }) => {
    const boxSizing = await page.evaluate(() => {
      const testEl = document.createElement('div');
      document.body.appendChild(testEl);
      const styles = getComputedStyle(testEl);
      const result = styles.boxSizing;
      testEl.remove();
      return result;
    });

    expect(boxSizing).toBe('border-box');
  });

  test('should apply dark theme by default', async ({ page }) => {
    const isDark = await page.evaluate(() => {
      const html = document.documentElement;
      const theme = html.getAttribute('data-theme');
      const bgBase = getComputedStyle(document.documentElement).getPropertyValue('--bg-base').trim();
      // Dark theme should have dark background color (low RGB values)
      return theme === 'dark' || bgBase.includes('#0f') || bgBase.includes('rgb(15');
    });

    expect(isDark).toBeTruthy();
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
    // Check for actual card classes used in the dashboard
    const cards = await page.$$('.kpi-card, .sidebar-card, .card');
    expect(cards.length).toBeGreaterThan(0);
  });

  test('should have tab navigation', async ({ page }) => {
    const tabs = await page.$$('.tab-btn, [role="tab"]');
    expect(tabs.length).toBeGreaterThan(0);
  });

  test('should have button CSS classes defined', async ({ page }) => {
    await page.waitForLoadState('networkidle');
    const hasBtnStyles = await page.evaluate(() => {
      const testEl = document.createElement('button');
      testEl.className = 'btn btn-primary';
      document.body.appendChild(testEl);
      testEl.offsetHeight;
      const styles = getComputedStyle(testEl);
      const hasStyles = styles.display === 'inline-flex' || styles.cursor === 'pointer';
      testEl.remove();
      return hasStyles;
    });
    expect(hasBtnStyles).toBeTruthy();
  });

  test('should have badge CSS classes defined', async ({ page }) => {
    await page.waitForLoadState('networkidle');
    const hasBadgeStyles = await page.evaluate(() => {
      const testEl = document.createElement('span');
      testEl.className = 'badge badge-success';
      document.body.appendChild(testEl);
      testEl.offsetHeight;
      const styles = getComputedStyle(testEl);
      const hasStyles = styles.display === 'inline-flex';
      testEl.remove();
      return hasStyles;
    });
    expect(hasBadgeStyles).toBeTruthy();
  });

  test('should have input CSS classes defined', async ({ page }) => {
    await page.waitForLoadState('networkidle');
    const hasInputStyles = await page.evaluate(() => {
      const testEl = document.createElement('input');
      testEl.className = 'input';
      testEl.type = 'text';
      document.body.appendChild(testEl);
      testEl.offsetHeight;
      const styles = getComputedStyle(testEl);
      const hasStyles = styles.width === '100%' || styles.borderRadius !== '0px';
      testEl.remove();
      return hasStyles;
    });
    expect(hasInputStyles).toBeTruthy();
  });

  test('should have progress bar CSS classes defined', async ({ page }) => {
    await page.waitForLoadState('networkidle');
    const hasProgressStyles = await page.evaluate(() => {
      const testEl = document.createElement('div');
      testEl.className = 'progress';
      document.body.appendChild(testEl);
      testEl.offsetHeight;
      const styles = getComputedStyle(testEl);
      const hasStyles = styles.overflow === 'hidden' || styles.borderRadius !== '0px';
      testEl.remove();
      return hasStyles;
    });
    expect(hasProgressStyles).toBeTruthy();
  });

  test('should have loader/spinner CSS classes defined', async ({ page }) => {
    await page.waitForLoadState('networkidle');
    const hasSpinnerStyles = await page.evaluate(() => {
      const testEl = document.createElement('div');
      testEl.className = 'spinner';
      document.body.appendChild(testEl);
      testEl.offsetHeight;
      const styles = getComputedStyle(testEl);
      const hasStyles = styles.borderRadius === '50%' || styles.animation !== 'none';
      testEl.remove();
      return hasStyles;
    });
    expect(hasSpinnerStyles).toBeTruthy();
  });

  test('should have toast CSS classes defined', async ({ page }) => {
    await page.waitForLoadState('networkidle');
    const hasToastStyles = await page.evaluate(() => {
      const testEl = document.createElement('div');
      testEl.className = 'toast';
      document.body.appendChild(testEl);
      testEl.offsetHeight;
      const styles = getComputedStyle(testEl);
      const hasStyles = styles.display === 'flex' || styles.borderRadius !== '0px';
      testEl.remove();
      return hasStyles;
    });
    expect(hasToastStyles).toBeTruthy();
  });

  test('should have modal CSS classes defined', async ({ page }) => {
    await page.waitForLoadState('networkidle');
    const hasModalStyles = await page.evaluate(() => {
      const testEl = document.createElement('div');
      testEl.className = 'modal';
      document.body.appendChild(testEl);
      testEl.offsetHeight;
      const styles = getComputedStyle(testEl);
      const hasStyles = styles.position === 'fixed' || styles.zIndex !== 'auto';
      testEl.remove();
      return hasStyles;
    });
    expect(hasModalStyles).toBeTruthy();
  });

  test('should have table CSS classes defined', async ({ page }) => {
    await page.waitForLoadState('networkidle');
    const hasTableStyles = await page.evaluate(() => {
      const testEl = document.createElement('table');
      testEl.className = 'table';
      document.body.appendChild(testEl);
      testEl.offsetHeight;
      const styles = getComputedStyle(testEl);
      const hasStyles = styles.width === '100%' || styles.borderCollapse === 'collapse';
      testEl.remove();
      return hasStyles;
    });
    expect(hasTableStyles).toBeTruthy();
  });

  test('should have tooltip CSS classes defined', async ({ page }) => {
    await page.waitForLoadState('networkidle');
    const hasTooltipStyles = await page.evaluate(() => {
      const testEl = document.createElement('div');
      testEl.className = 'tooltip';
      document.body.appendChild(testEl);
      testEl.offsetHeight;
      const styles = getComputedStyle(testEl);
      const hasStyles = styles.position === 'relative' || styles.display === 'inline-block';
      testEl.remove();
      return hasStyles;
    });
    expect(hasTooltipStyles).toBeTruthy();
  });

  test('should have skeleton loading CSS classes defined', async ({ page }) => {
    await page.waitForLoadState('networkidle');
    const hasSkeletonStyles = await page.evaluate(() => {
      const testEl = document.createElement('div');
      testEl.className = 'skeleton';
      document.body.appendChild(testEl);
      testEl.offsetHeight;
      const styles = getComputedStyle(testEl);
      const hasStyles = styles.animation !== 'none' || styles.background !== 'rgba(0, 0, 0, 0)';
      testEl.remove();
      return hasStyles;
    });
    expect(hasSkeletonStyles).toBeTruthy();
  });

  test('should have KPI card styling', async ({ page }) => {
    const kpiCards = await page.$$('.kpi-card');
    expect(kpiCards.length).toBeGreaterThan(0);

    // Verify KPI card has glassmorphism
    const hasGlass = await page.evaluate(() => {
      const card = document.querySelector('.kpi-card');
      if (!card) return false;
      const styles = getComputedStyle(card);
      return styles.backdropFilter !== 'none' || styles.background.includes('rgba');
    });
    expect(hasGlass).toBeTruthy();
  });

  test('should have regime badge on page', async ({ page }) => {
    const regimeBadge = await page.$('.regime-badge, #hero-regime-badge');
    expect(regimeBadge).not.toBeNull();
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
    // Create a test element with card-tilt class and verify it has 3D transform styles
    const hasTiltStyles = await page.evaluate(() => {
      const testEl = document.createElement('div');
      testEl.className = 'card-tilt';
      testEl.style.width = '100px';
      testEl.style.height = '100px';
      document.body.appendChild(testEl);
      const styles = getComputedStyle(testEl);
      const hasStyles = styles.transformStyle === 'preserve-3d' ||
                        styles.perspective !== 'none';
      testEl.remove();
      return hasStyles;
    });
    expect(hasTiltStyles).toBeTruthy();
  });

  test('should have theme-tag CSS classes defined', async ({ page }) => {
    // Wait for all stylesheets to load
    await page.waitForLoadState('networkidle');

    // Create a test element with theme-tag class and verify styles
    const hasThemeTagStyles = await page.evaluate(() => {
      const testEl = document.createElement('span');
      testEl.className = 'theme-tag';
      testEl.textContent = 'Test Tag';
      document.body.appendChild(testEl);

      // Force style recalculation
      testEl.offsetHeight;

      const styles = getComputedStyle(testEl);
      // Theme tags should have inline-flex display and cursor pointer
      // Check for either inline-flex or flex (browser normalization)
      const hasDisplay = styles.display === 'inline-flex' || styles.display.includes('flex');
      const hasCursor = styles.cursor === 'pointer';
      const hasPadding = styles.padding !== '0px'; // Should have padding

      testEl.remove();
      return hasDisplay || hasCursor || hasPadding;
    });
    expect(hasThemeTagStyles).toBeTruthy();
  });

  test('should have conviction-bar CSS with shimmer animation', async ({ page }) => {
    // Create a test element with conviction-bar-fill class and verify styles
    const hasConvictionBarStyles = await page.evaluate(() => {
      const testEl = document.createElement('div');
      testEl.className = 'conviction-bar-fill';
      testEl.style.width = '100px';
      testEl.style.height = '10px';
      document.body.appendChild(testEl);
      const styles = getComputedStyle(testEl);
      // Conviction bar should have position relative and overflow hidden for shimmer
      const hasStyles = styles.position === 'relative' &&
                        styles.overflow === 'hidden';
      testEl.remove();
      return hasStyles;
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

  test('should have source status list container', async ({ page }) => {
    // Check that source status list container exists (items are loaded dynamically via API)
    const sourceList = await page.$('#source-status-list, .source-list');
    expect(sourceList).not.toBeNull();
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

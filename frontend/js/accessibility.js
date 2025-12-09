/**
 * Accessibility Enhancement Module
 * Manages ARIA attributes, announcements, and keyboard navigation
 */

const AccessibilityManager = {
  liveRegion: null,

  /**
   * Initialize accessibility features
   */
  init() {
    this.createLiveRegion();
    this.enhanceInteractiveElements();
    this.setupKeyboardNavigation();
    this.setupFocusManagement();
    this.setupReducedMotion();

    console.log('[A11y] Accessibility manager initialized');
  },

  /**
   * Create ARIA live region for announcements
   */
  createLiveRegion() {
    if (document.getElementById('a11y-announcer')) return;

    this.liveRegion = document.createElement('div');
    this.liveRegion.id = 'a11y-announcer';
    this.liveRegion.setAttribute('role', 'status');
    this.liveRegion.setAttribute('aria-live', 'polite');
    this.liveRegion.setAttribute('aria-atomic', 'true');
    this.liveRegion.className = 'sr-only';
    document.body.appendChild(this.liveRegion);
  },

  /**
   * Announce message to screen readers
   */
  announce(message, priority = 'polite') {
    if (!this.liveRegion) return;

    this.liveRegion.setAttribute('aria-live', priority);
    this.liveRegion.textContent = '';

    setTimeout(() => {
      this.liveRegion.textContent = message;
    }, 100);
  },

  /**
   * Enhance interactive elements with proper ARIA
   */
  enhanceInteractiveElements() {
    document.querySelectorAll('.card-interactive:not([role])').forEach(card => {
      card.setAttribute('role', 'button');
      card.setAttribute('tabindex', '0');
    });

    document.querySelectorAll('.tab-panel').forEach(panel => {
      panel.setAttribute('role', 'tabpanel');
      if (!panel.hasAttribute('aria-labelledby')) {
        const tabId = panel.id?.replace('-panel', '-tab');
        if (tabId) panel.setAttribute('aria-labelledby', tabId);
      }
    });

    document.querySelectorAll('.spinner, .loader').forEach(loader => {
      loader.setAttribute('role', 'status');
      loader.setAttribute('aria-label', 'Loading');
    });

    document.querySelectorAll('.badge-status').forEach(badge => {
      badge.setAttribute('role', 'status');
    });
  },

  /**
   * Setup keyboard navigation
   */
  setupKeyboardNavigation() {
    document.addEventListener('keydown', (e) => {
      // Skip to main content (Alt + 1)
      if (e.altKey && e.key === '1') {
        e.preventDefault();
        const main = document.querySelector('main, [role="main"], .main');
        if (main) {
          main.setAttribute('tabindex', '-1');
          main.focus();
          this.announce('Skipped to main content');
        }
      }

      // Open search (Cmd/Ctrl + K)
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        const searchModal = document.getElementById('search-modal');
        if (searchModal) {
          this.openModal(searchModal);
          this.announce('Search opened');
        }
      }

      // Close modals/drawers (Escape)
      if (e.key === 'Escape') {
        const activeModal = document.querySelector('.modal-backdrop.active');
        const activeDrawer = document.querySelector('.drawer.open');

        if (activeModal) {
          this.closeModal(activeModal);
          this.announce('Modal closed');
        } else if (activeDrawer) {
          this.closeDrawer(activeDrawer);
          this.announce('Menu closed');
        }
      }

      // Arrow key navigation for tabs
      if (['ArrowLeft', 'ArrowRight'].includes(e.key)) {
        const activeTab = document.activeElement;
        if (activeTab?.getAttribute('role') === 'tab') {
          this.navigateTabs(activeTab, e.key);
        }
      }
    });

    // Enter/Space activation for custom buttons
    document.addEventListener('keydown', (e) => {
      if (['Enter', ' '].includes(e.key)) {
        const target = e.target;
        if (target.getAttribute('role') === 'button' && target.tagName !== 'BUTTON') {
          e.preventDefault();
          target.click();
        }
      }
    });
  },

  /**
   * Navigate tabs with arrow keys
   */
  navigateTabs(currentTab, direction) {
    const tablist = currentTab.closest('[role="tablist"]');
    if (!tablist) return;

    const tabs = Array.from(tablist.querySelectorAll('[role="tab"]'));
    const currentIndex = tabs.indexOf(currentTab);

    let nextIndex;
    if (direction === 'ArrowRight') {
      nextIndex = currentIndex === tabs.length - 1 ? 0 : currentIndex + 1;
    } else {
      nextIndex = currentIndex === 0 ? tabs.length - 1 : currentIndex - 1;
    }

    tabs[nextIndex].focus();
    tabs[nextIndex].click();
  },

  /**
   * Setup focus management
   */
  setupFocusManagement() {
    // Show focus outline only for keyboard users
    document.body.addEventListener('mousedown', () => {
      document.body.classList.add('using-mouse');
    });

    document.body.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        document.body.classList.remove('using-mouse');
      }
    });

    // Focus trap for modals
    document.addEventListener('focusin', (e) => {
      const activeModal = document.querySelector('.modal-backdrop.active .modal-content');
      if (activeModal && !activeModal.contains(e.target)) {
        const focusable = activeModal.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length) {
          focusable[0].focus();
        }
      }
    });
  },

  /**
   * Setup reduced motion support
   */
  setupReducedMotion() {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    const handleReducedMotion = (e) => {
      if (e.matches) {
        document.body.classList.add('reduce-motion');
      } else {
        document.body.classList.remove('reduce-motion');
      }
    };

    handleReducedMotion(mediaQuery);
    mediaQuery.addEventListener('change', handleReducedMotion);
  },

  /**
   * Open modal with focus management
   */
  openModal(modal) {
    modal.dataset.previousFocus = document.activeElement?.id || '';
    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');

    const focusable = modal.querySelector(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (focusable) {
      setTimeout(() => focusable.focus(), 100);
    }
  },

  /**
   * Close modal with focus restoration
   */
  closeModal(modal) {
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');

    const previousFocusId = modal.dataset.previousFocus;
    if (previousFocusId) {
      const previousElement = document.getElementById(previousFocusId);
      if (previousElement) previousElement.focus();
    }
  },

  /**
   * Close drawer
   */
  closeDrawer(drawer) {
    drawer.classList.remove('open');
    drawer.setAttribute('aria-hidden', 'true');
  },

  /**
   * Update loading state with announcement
   */
  setLoading(isLoading, message = '') {
    if (isLoading) {
      this.announce(message || 'Loading content, please wait');
    } else {
      this.announce(message || 'Content loaded');
    }
  },

  /**
   * Announce data update
   */
  announceUpdate(type, details = '') {
    const messages = {
      synthesis: `Research synthesis updated. ${details}`,
      themes: `Theme data updated. ${details}`,
      error: `Error: ${details}`,
      success: `Success: ${details}`
    };

    this.announce(messages[type] || details, type === 'error' ? 'assertive' : 'polite');
  }
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => AccessibilityManager.init());
} else {
  AccessibilityManager.init();
}

// Export for module usage
window.AccessibilityManager = AccessibilityManager;

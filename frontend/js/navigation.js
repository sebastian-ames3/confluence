/**
 * Navigation & Layout JavaScript (PRD-029)
 * Handles mobile menu, search modal, tabs, scroll behavior
 */

// ============================================
// MOBILE NAVIGATION
// ============================================
const mobileNav = {
  nav: null,
  menuBtn: null,
  closeBtn: null,
  overlay: null,

  init() {
    this.nav = document.getElementById('mobile-nav');
    this.menuBtn = document.getElementById('mobile-menu-btn');
    this.closeBtn = document.getElementById('mobile-nav-close');
    this.overlay = document.querySelector('.mobile-nav-overlay');

    if (!this.nav || !this.menuBtn) return;

    this.menuBtn.addEventListener('click', () => this.toggle());
    this.closeBtn?.addEventListener('click', () => this.close());
    this.overlay?.addEventListener('click', () => this.close());

    // Close on escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.nav.classList.contains('active')) {
        this.close();
      }
    });

    // Close on link click
    this.nav.querySelectorAll('.mobile-nav-link').forEach(link => {
      link.addEventListener('click', () => this.close());
    });
  },

  toggle() {
    this.nav.classList.toggle('active');
    this.menuBtn.classList.toggle('active');
    document.body.style.overflow = this.nav.classList.contains('active') ? 'hidden' : '';
  },

  close() {
    this.nav.classList.remove('active');
    this.menuBtn.classList.remove('active');
    document.body.style.overflow = '';
  }
};

// ============================================
// SEARCH MODAL
// ============================================
const searchModal = {
  modal: null,
  trigger: null,
  input: null,

  init() {
    this.modal = document.getElementById('search-modal');
    this.trigger = document.getElementById('search-trigger');

    if (!this.modal) return;

    this.input = this.modal.querySelector('.search-modal-input');
    const backdrop = this.modal.querySelector('.modal-backdrop');

    // Open on trigger click
    this.trigger?.addEventListener('click', () => this.open());

    // Open on Cmd/Ctrl + K
    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        this.open();
      }
    });

    // Close on escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.modal.classList.contains('active')) {
        this.close();
      }
    });

    // Close on backdrop click
    backdrop?.addEventListener('click', () => this.close());

    // Handle search input
    this.input?.addEventListener('input', (e) => this.handleSearch(e.target.value));
  },

  open() {
    this.modal.classList.add('active');
    this.modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    this.input?.focus();
  },

  close() {
    this.modal.classList.remove('active');
    this.modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    if (this.input) this.input.value = '';
    this.clearResults();
  },

  handleSearch(query) {
    // Placeholder for search functionality
    // This would integrate with your API
    if (query.length < 2) {
      this.clearResults();
      return;
    }
    console.log('[Search] Query:', query);
  },

  clearResults() {
    const results = document.getElementById('search-results');
    if (results) results.innerHTML = '';
  }
};

// ============================================
// TAB NAVIGATION
// ============================================
const tabNav = {
  init() {
    const tabButtons = document.querySelectorAll('.tab-btn[data-tab]');
    const tabPanels = document.querySelectorAll('.tab-panel');

    tabButtons.forEach(button => {
      button.addEventListener('click', () => {
        const tabId = button.dataset.tab;

        // Update button states
        tabButtons.forEach(btn => {
          btn.classList.remove('active');
          btn.setAttribute('aria-selected', 'false');
        });
        button.classList.add('active');
        button.setAttribute('aria-selected', 'true');

        // Update panel visibility
        tabPanels.forEach(panel => {
          panel.classList.remove('active');
        });
        const targetPanel = document.getElementById(`panel-${tabId}`);
        targetPanel?.classList.add('active');

        // Update URL hash without scrolling
        history.replaceState(null, '', `#${tabId}`);

        // Dispatch event for other components
        window.dispatchEvent(new CustomEvent('tabchange', { detail: { tab: tabId } }));
      });
    });

    // Handle initial hash
    const hash = window.location.hash.slice(1);
    if (hash) {
      const targetTab = document.querySelector(`.tab-btn[data-tab="${hash}"]`);
      targetTab?.click();
    }
  }
};

// ============================================
// HEADER SCROLL BEHAVIOR
// ============================================
const headerScroll = {
  header: null,
  fab: null,
  lastScroll: 0,

  init() {
    this.header = document.getElementById('site-header');
    this.fab = document.getElementById('floating-actions');

    if (!this.header) return;

    window.addEventListener('scroll', () => this.handleScroll(), { passive: true });
  },

  handleScroll() {
    const currentScroll = window.scrollY;

    // Add shadow on scroll
    if (currentScroll > 10) {
      this.header.classList.add('scrolled');
    } else {
      this.header.classList.remove('scrolled');
    }

    // Hide FAB on scroll down, show on scroll up
    if (this.fab) {
      if (currentScroll > this.lastScroll && currentScroll > 200) {
        this.fab.classList.add('hidden');
      } else {
        this.fab.classList.remove('hidden');
      }
    }

    this.lastScroll = currentScroll;
  }
};

// ============================================
// SMOOTH SCROLL FOR ANCHOR LINKS
// ============================================
const smoothScroll = {
  init() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', (e) => {
        const href = anchor.getAttribute('href');
        if (href === '#') return;

        const target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      });
    });
  }
};

// ============================================
// SKIP LINK FOCUS HANDLING
// ============================================
const skipLink = {
  init() {
    const skip = document.querySelector('.skip-link');
    if (!skip) return;

    skip.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(skip.getAttribute('href'));
      if (target) {
        target.setAttribute('tabindex', '-1');
        target.focus();
        target.removeAttribute('tabindex');
      }
    });
  }
};

// ============================================
// INITIALIZE ALL
// ============================================
function initNavigation() {
  mobileNav.init();
  searchModal.init();
  tabNav.init();
  headerScroll.init();
  smoothScroll.init();
  skipLink.init();

  console.log('[Nav] Navigation initialized');
}

// Auto-init on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initNavigation);
} else {
  initNavigation();
}

// Export for external use
window.navigation = {
  mobileNav,
  searchModal,
  tabNav,
  headerScroll
};

/**
 * Animation Controller
 * Manages page animations, transitions, and micro-interactions
 */

const AnimationController = {
  config: {
    observerThreshold: 0.1,
    staggerDelay: 50,
    reducedMotion: false
  },

  /**
   * Initialize animation system
   */
  init() {
    this.config.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
      this.config.reducedMotion = e.matches;
    });

    this.setupScrollAnimations();
    this.setupRippleEffects();
    this.animatePageLoad();
    this.setupTabTransitions();

    console.log('[Animations] Controller initialized');
  },

  /**
   * Setup intersection observer for scroll-triggered animations
   */
  setupScrollAnimations() {
    if (this.config.reducedMotion) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate');
          if (entry.target.dataset.animateOnce !== 'false') {
            observer.unobserve(entry.target);
          }
        }
      });
    }, {
      threshold: this.config.observerThreshold,
      rootMargin: '0px 0px -50px 0px'
    });

    document.querySelectorAll('.stagger-container, .hero-section, .kpi-grid, [data-animate]').forEach(el => {
      observer.observe(el);
    });

    this.scrollObserver = observer;
  },

  /**
   * Setup material-design ripple effects on buttons
   */
  setupRippleEffects() {
    document.addEventListener('click', (e) => {
      const button = e.target.closest('.btn, .card-interactive, [data-ripple]');
      if (!button || this.config.reducedMotion) return;

      const ripple = document.createElement('span');
      ripple.className = 'ripple-effect';

      const rect = button.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;

      ripple.style.cssText = `
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
      `;

      button.appendChild(ripple);

      ripple.addEventListener('animationend', () => {
        ripple.remove();
      });
    });
  },

  /**
   * Animate page load
   */
  animatePageLoad() {
    if (this.config.reducedMotion) {
      document.body.classList.add('page-ready');
      return;
    }

    requestAnimationFrame(() => {
      document.body.classList.remove('page-loading');
      document.body.classList.add('page-ready');

      const hero = document.querySelector('.hero-section, .hero');
      if (hero) {
        setTimeout(() => hero.classList.add('animate'), 100);
      }

      const kpiGrid = document.querySelector('.kpi-grid');
      if (kpiGrid) {
        setTimeout(() => kpiGrid.classList.add('animate'), 300);
      }
    });
  },

  /**
   * Setup smooth tab transitions
   */
  setupTabTransitions() {
    document.querySelectorAll('[role="tab"]').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const targetId = tab.getAttribute('aria-controls');
        const targetPanel = document.getElementById(targetId);
        const currentPanel = document.querySelector('[role="tabpanel"][aria-hidden="false"], [role="tabpanel"].active');

        if (currentPanel && targetPanel && currentPanel !== targetPanel) {
          this.transitionPanels(currentPanel, targetPanel);
        }
      });
    });
  },

  /**
   * Transition between panels with animation
   */
  transitionPanels(fromPanel, toPanel) {
    if (this.config.reducedMotion) {
      fromPanel.classList.remove('active');
      fromPanel.setAttribute('aria-hidden', 'true');
      toPanel.classList.add('active');
      toPanel.setAttribute('aria-hidden', 'false');
      return;
    }

    fromPanel.style.opacity = '0';
    fromPanel.style.transform = 'translateY(10px)';

    setTimeout(() => {
      fromPanel.classList.remove('active');
      fromPanel.setAttribute('aria-hidden', 'true');
      fromPanel.style.cssText = '';

      toPanel.classList.add('active');
      toPanel.setAttribute('aria-hidden', 'false');

      toPanel.querySelectorAll('.stagger-container').forEach(container => {
        container.classList.remove('animate');
        requestAnimationFrame(() => {
          container.classList.add('animate');
        });
      });
    }, 200);
  },

  /**
   * Animate element entrance
   */
  animateIn(element, animation = 'fade-in') {
    if (this.config.reducedMotion) {
      element.style.opacity = '1';
      return Promise.resolve();
    }

    return new Promise(resolve => {
      element.classList.add(`animate-${animation}`);
      element.addEventListener('animationend', () => {
        resolve();
      }, { once: true });
    });
  },

  /**
   * Animate element exit
   */
  animateOut(element, animation = 'fade-out') {
    if (this.config.reducedMotion) {
      element.style.opacity = '0';
      return Promise.resolve();
    }

    return new Promise(resolve => {
      element.classList.add(`animate-${animation}`);
      element.addEventListener('animationend', () => {
        element.classList.remove(`animate-${animation}`);
        resolve();
      }, { once: true });
    });
  },

  /**
   * Stagger animate children
   */
  staggerChildren(parent, animation = 'slide-up', delay = 50) {
    if (this.config.reducedMotion) return;

    const children = Array.from(parent.children);
    children.forEach((child, index) => {
      child.style.animationDelay = `${index * delay}ms`;
      child.classList.add(`animate-${animation}`);
    });
  },

  /**
   * Show success feedback
   */
  showSuccess(element) {
    element.classList.add('feedback-success');
    setTimeout(() => element.classList.remove('feedback-success'), 500);
  },

  /**
   * Show error feedback
   */
  showError(element) {
    element.classList.add('feedback-error', 'animate-shake');
    setTimeout(() => {
      element.classList.remove('feedback-error', 'animate-shake');
    }, 500);
  },

  /**
   * Set button loading state
   */
  setButtonLoading(button, loading = true) {
    if (loading) {
      button.classList.add('loading');
      button.dataset.originalText = button.textContent;
      button.disabled = true;
    } else {
      button.classList.remove('loading');
      if (button.dataset.originalText) {
        button.textContent = button.dataset.originalText;
        delete button.dataset.originalText;
      }
      button.disabled = false;
    }
  },

  /**
   * Show refresh indicator
   */
  showRefreshIndicator(show = true) {
    let indicator = document.querySelector('.refresh-indicator');
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.className = 'refresh-indicator';
      indicator.innerHTML = '<div class="spinner spinner-sm"></div><span>Updating...</span>';
      document.body.appendChild(indicator);
    }

    if (show) {
      requestAnimationFrame(() => indicator.classList.add('visible'));
    } else {
      indicator.classList.remove('visible');
    }
  }
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => AnimationController.init());
} else {
  AnimationController.init();
}

// Export for module usage
window.AnimationController = AnimationController;

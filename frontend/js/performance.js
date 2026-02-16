/**
 * Performance Optimization Module
 * Handles lazy loading, caching, and performance monitoring
 */

const PerformanceManager = {
  // Performance metrics
  metrics: {
    fcp: null,      // First Contentful Paint
    lcp: null,      // Largest Contentful Paint
    fid: null,      // First Input Delay
    cls: null,      // Cumulative Layout Shift
    ttfb: null      // Time to First Byte
  },

  // Cache for API responses
  cache: new Map(),
  cacheExpiry: 5 * 60 * 1000, // 5 minutes

  /**
   * Initialize performance optimizations
   */
  init() {
    this.setupLazyLoading();
    this.setupResourceHints();
    this.measureWebVitals();
    this.setupIdleCallback();

    console.log('[Perf] Performance manager initialized');
  },

  /**
   * Setup lazy loading for images and iframes
   */
  setupLazyLoading() {
    // Native lazy loading for images
    document.querySelectorAll('img[data-src]').forEach(img => {
      img.loading = 'lazy';
      img.src = img.dataset.src;
    });

    // Intersection Observer for custom lazy loading
    const lazyObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;

          // Load background images
          if (el.dataset.bg) {
            el.style.backgroundImage = `url(${el.dataset.bg})`;
            el.classList.add('loaded');
          }

          // Load iframes
          if (el.tagName === 'IFRAME' && el.dataset.src) {
            el.src = el.dataset.src;
          }

          lazyObserver.unobserve(el);
        }
      });
    }, {
      rootMargin: '100px',
      threshold: 0.01
    });

    document.querySelectorAll('[data-bg], iframe[data-src]').forEach(el => {
      lazyObserver.observe(el);
    });

    this.lazyObserver = lazyObserver;
  },

  /**
   * Setup resource hints for faster loading
   */
  setupResourceHints() {
    // Preconnect to API domain
    this.addResourceHint('preconnect', 'https://confluence-production-a32e.up.railway.app');

    // Prefetch likely next pages (only if authenticated)
    if ('requestIdleCallback' in window && localStorage.getItem('confluence_auth_token')) {
      requestIdleCallback(() => {
        // Prefetch dashboard data
        this.prefetchData('/api/dashboard/today');
      });
    }
  },

  /**
   * Add resource hint to head
   */
  addResourceHint(rel, href, as = null) {
    if (document.querySelector(`link[href="${href}"]`)) return;

    const link = document.createElement('link');
    link.rel = rel;
    link.href = href;
    if (as) link.as = as;
    if (rel === 'preconnect') link.crossOrigin = 'anonymous';

    document.head.appendChild(link);
  },

  /**
   * Measure Web Vitals
   */
  measureWebVitals() {
    // First Contentful Paint
    try {
      const paintObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.name === 'first-contentful-paint') {
            this.metrics.fcp = entry.startTime;
            console.log(`[Perf] FCP: ${entry.startTime.toFixed(2)}ms`);
          }
        }
      });
      paintObserver.observe({ type: 'paint', buffered: true });
    } catch (e) {
      // Observer not supported
    }

    // Largest Contentful Paint
    try {
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        this.metrics.lcp = lastEntry.startTime;
        console.log(`[Perf] LCP: ${lastEntry.startTime.toFixed(2)}ms`);
      });
      lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
    } catch (e) {
      // Observer not supported
    }

    // First Input Delay
    try {
      const fidObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.metrics.fid = entry.processingStart - entry.startTime;
          console.log(`[Perf] FID: ${this.metrics.fid.toFixed(2)}ms`);
        }
      });
      fidObserver.observe({ type: 'first-input', buffered: true });
    } catch (e) {
      // Observer not supported
    }

    // Cumulative Layout Shift
    try {
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
          }
        }
        this.metrics.cls = clsValue;
      });
      clsObserver.observe({ type: 'layout-shift', buffered: true });
    } catch (e) {
      // Observer not supported
    }

    // Time to First Byte
    const navigation = performance.getEntriesByType('navigation')[0];
    if (navigation) {
      this.metrics.ttfb = navigation.responseStart - navigation.requestStart;
      console.log(`[Perf] TTFB: ${this.metrics.ttfb.toFixed(2)}ms`);
    }
  },

  /**
   * Setup idle callback for non-critical work
   */
  setupIdleCallback() {
    if (!('requestIdleCallback' in window)) {
      // Polyfill for Safari
      window.requestIdleCallback = (callback) => {
        return setTimeout(() => {
          callback({
            didTimeout: false,
            timeRemaining: () => 50
          });
        }, 1);
      };
    }

    // Queue non-critical initialization
    requestIdleCallback(() => {
      // Initialize charts lazily
      if (typeof ChartsManager !== 'undefined') {
        ChartsManager.init();
      }

      // Preload fonts
      this.preloadFonts();
    });
  },

  /**
   * Preload fonts
   */
  preloadFonts() {
    const fonts = [
      { family: 'Inter', weight: '400' },
      { family: 'Inter', weight: '500' },
      { family: 'Inter', weight: '600' },
      { family: 'JetBrains Mono', weight: '400' }
    ];

    fonts.forEach(({ family, weight }) => {
      try {
        const font = new FontFace(family, `local('${family}')`, { weight });
        font.load().catch(() => {
          // Font not available locally, will load from Google Fonts
        });
      } catch (e) {
        // FontFace API not supported
      }
    });
  },

  /**
   * Cached fetch with expiry
   */
  async cachedFetch(url, options = {}) {
    const cacheKey = `${url}-${JSON.stringify(options)}`;
    const cached = this.cache.get(cacheKey);

    if (cached && Date.now() - cached.timestamp < this.cacheExpiry) {
      return cached.data;
    }

    const response = await fetch(url, options);
    const data = await response.json();

    this.cache.set(cacheKey, {
      data,
      timestamp: Date.now()
    });

    return data;
  },

  /**
   * Prefetch data for faster navigation
   */
  async prefetchData(url) {
    try {
      await this.cachedFetch(url);
    } catch (e) {
      // Silently fail prefetch
    }
  },

  /**
   * Debounce function for scroll/resize handlers
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  /**
   * Throttle function for high-frequency events
   */
  throttle(func, limit) {
    let inThrottle;
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },

  /**
   * Get current performance metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      memory: performance.memory ? {
        usedJSHeapSize: (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + 'MB',
        totalJSHeapSize: (performance.memory.totalJSHeapSize / 1048576).toFixed(2) + 'MB'
      } : null
    };
  },

  /**
   * Clear expired cache entries
   */
  clearExpiredCache() {
    const now = Date.now();
    for (const [key, value] of this.cache) {
      if (now - value.timestamp > this.cacheExpiry) {
        this.cache.delete(key);
      }
    }
  }
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => PerformanceManager.init());
} else {
  PerformanceManager.init();
}

// Clear cache periodically
setInterval(() => PerformanceManager.clearExpiredCache(), 60000);

// Export
window.PerformanceManager = PerformanceManager;

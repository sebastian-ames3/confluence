/**
 * Toast Notification System
 * Modern toast notifications with animations
 */

const ToastManager = {
  container: null,
  toasts: [],
  defaultDuration: 5000,

  /**
   * Initialize toast system
   */
  init() {
    this.createContainer();
    console.log('[Toast] Manager initialized');
  },

  /**
   * Create toast container
   */
  createContainer() {
    if (document.getElementById('toast-container')) {
      this.container = document.getElementById('toast-container');
      return;
    }

    this.container = document.createElement('div');
    this.container.id = 'toast-container';
    this.container.className = 'toast-container toast-container-top-right';
    document.body.appendChild(this.container);
  },

  /**
   * Show a toast notification
   */
  show(options) {
    const {
      title,
      message,
      type = 'info',
      duration = this.defaultDuration,
      actions = [],
      closable = true,
      icon = true
    } = typeof options === 'string' ? { message: options } : options;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const iconHtml = icon ? this.getIcon(type) : '';
    const closeHtml = closable ? `
      <button class="toast-close" aria-label="Close">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12"/>
        </svg>
      </button>
    ` : '';

    const actionsHtml = actions.length ? `
      <div class="toast-actions">
        ${actions.map(action => `
          <button class="toast-action toast-action-${sanitizeHTML(action.type || 'secondary')}" data-action="${sanitizeHTML(action.id || '')}">
            ${sanitizeHTML(action.label)}
          </button>
        `).join('')}
      </div>
    ` : '';

    toast.innerHTML = `
      ${iconHtml}
      <div class="toast-content">
        ${title ? `<div class="toast-title">${sanitizeHTML(title)}</div>` : ''}
        ${message ? `<div class="toast-message">${sanitizeHTML(message)}</div>` : ''}
        ${actionsHtml}
      </div>
      ${closeHtml}
      ${duration > 0 ? '<div class="toast-progress"><div class="toast-progress-bar"></div></div>' : ''}
    `;

    // Add event listeners
    if (closable) {
      toast.querySelector('.toast-close').addEventListener('click', () => this.dismiss(toast));
    }

    actions.forEach(action => {
      const btn = toast.querySelector(`[data-action="${action.id}"]`);
      if (btn && action.onClick) {
        btn.addEventListener('click', () => {
          action.onClick();
          this.dismiss(toast);
        });
      }
    });

    // Add to container
    this.container.appendChild(toast);
    this.toasts.push(toast);

    // Animate progress bar
    if (duration > 0) {
      const progressBar = toast.querySelector('.toast-progress-bar');
      progressBar.style.width = '100%';
      progressBar.style.transition = `width ${duration}ms linear`;
      requestAnimationFrame(() => {
        progressBar.style.width = '0%';
      });

      // Auto dismiss
      setTimeout(() => this.dismiss(toast), duration);
    }

    // Announce to screen readers
    if (typeof AccessibilityManager !== 'undefined') {
      AccessibilityManager.announce(`${type}: ${title || ''} ${message || ''}`);
    }

    return toast;
  },

  /**
   * Dismiss a toast
   */
  dismiss(toast) {
    if (!toast || toast.classList.contains('exiting')) return;

    toast.classList.add('exiting');

    toast.addEventListener('animationend', () => {
      toast.remove();
      this.toasts = this.toasts.filter(t => t !== toast);
    });
  },

  /**
   * Dismiss all toasts
   */
  dismissAll() {
    this.toasts.forEach(toast => this.dismiss(toast));
  },

  /**
   * Get icon SVG for toast type
   */
  getIcon(type) {
    const icons = {
      success: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
        <polyline points="22 4 12 14.01 9 11.01"/>
      </svg>`,
      error: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="15" y1="9" x2="9" y2="15"/>
        <line x1="9" y1="9" x2="15" y2="15"/>
      </svg>`,
      warning: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>`,
      info: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="16" x2="12" y2="12"/>
        <line x1="12" y1="8" x2="12.01" y2="8"/>
      </svg>`
    };

    return icons[type] || icons.info;
  },

  /**
   * Convenience methods
   */
  success(message, title = '') {
    return this.show({ type: 'success', message, title });
  },

  error(message, title = '') {
    return this.show({ type: 'error', message, title });
  },

  warning(message, title = '') {
    return this.show({ type: 'warning', message, title });
  },

  info(message, title = '') {
    return this.show({ type: 'info', message, title });
  }
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => ToastManager.init());
} else {
  ToastManager.init();
}

// Export
window.ToastManager = ToastManager;

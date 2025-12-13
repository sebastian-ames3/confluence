/**
 * Authentication Manager
 * Handles JWT-based session authentication for the dashboard.
 * Part of PRD-036: Session Authentication.
 */

const AuthManager = {
    // Storage keys
    TOKEN_KEY: 'confluence_auth_token',
    TOKEN_EXPIRES_KEY: 'confluence_auth_expires',
    USERNAME_KEY: 'confluence_auth_username',

    // Refresh threshold (60 minutes before expiry)
    REFRESH_THRESHOLD_MS: 60 * 60 * 1000,

    // Refresh timer reference
    refreshTimer: null,

    // ========================================================================
    // Token Management
    // ========================================================================

    /**
     * Get the stored access token
     * @returns {string|null} The access token or null
     */
    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    /**
     * Store the access token and expiration
     * @param {string} token - The JWT access token
     * @param {string} expiresAt - ISO timestamp of expiration
     * @param {string} username - The authenticated username
     */
    setToken(token, expiresAt, username) {
        localStorage.setItem(this.TOKEN_KEY, token);
        localStorage.setItem(this.TOKEN_EXPIRES_KEY, expiresAt);
        localStorage.setItem(this.USERNAME_KEY, username);
        this.scheduleRefresh();
    },

    /**
     * Clear stored authentication data
     */
    clearToken() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.TOKEN_EXPIRES_KEY);
        localStorage.removeItem(this.USERNAME_KEY);
        if (this.refreshTimer) {
            clearTimeout(this.refreshTimer);
            this.refreshTimer = null;
        }
    },

    /**
     * Get the stored username
     * @returns {string|null} The username or null
     */
    getUsername() {
        return localStorage.getItem(this.USERNAME_KEY);
    },

    /**
     * Check if user is logged in with valid token
     * @returns {boolean} True if logged in
     */
    isLoggedIn() {
        const token = this.getToken();
        const expiresAt = localStorage.getItem(this.TOKEN_EXPIRES_KEY);

        if (!token || !expiresAt) {
            return false;
        }

        // Check if token has expired
        const expiration = new Date(expiresAt);
        return expiration > new Date();
    },

    /**
     * Check if token is expiring soon
     * @returns {boolean} True if expires within threshold
     */
    isTokenExpiringSoon() {
        const expiresAt = localStorage.getItem(this.TOKEN_EXPIRES_KEY);
        if (!expiresAt) return true;

        const expiration = new Date(expiresAt);
        const threshold = new Date(Date.now() + this.REFRESH_THRESHOLD_MS);
        return expiration <= threshold;
    },

    // ========================================================================
    // Authentication Actions
    // ========================================================================

    /**
     * Login with username and password
     * @param {string} username - The username
     * @param {string} password - The password
     * @returns {Promise<Object>} The login response
     */
    async login(username, password) {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Login failed' }));
            throw new Error(error.detail || 'Invalid username or password');
        }

        const data = await response.json();
        this.setToken(data.access_token, data.expires_at, data.username);
        this.updateUI();
        return data;
    },

    /**
     * Logout the current user
     */
    async logout() {
        const token = this.getToken();
        if (token) {
            // Notify server (optional, since we're stateless)
            try {
                await fetch(`${API_BASE}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });
            } catch (e) {
                // Ignore logout errors
            }
        }

        this.clearToken();
        this.updateUI();
        this.showLoginModal();
    },

    /**
     * Refresh the current token
     * @returns {Promise<Object>} The refresh response
     */
    async refreshToken() {
        const token = this.getToken();
        if (!token) {
            throw new Error('No token to refresh');
        }

        const response = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            // Refresh failed, user needs to login again
            this.clearToken();
            this.showLoginModal();
            throw new Error('Session expired, please login again');
        }

        const data = await response.json();
        this.setToken(data.access_token, data.expires_at, data.username);
        return data;
    },

    // ========================================================================
    // Auto-Refresh
    // ========================================================================

    /**
     * Schedule token refresh before expiration
     */
    scheduleRefresh() {
        if (this.refreshTimer) {
            clearTimeout(this.refreshTimer);
        }

        const expiresAt = localStorage.getItem(this.TOKEN_EXPIRES_KEY);
        if (!expiresAt) return;

        const expiration = new Date(expiresAt);
        const now = new Date();
        const msUntilRefresh = expiration - now - this.REFRESH_THRESHOLD_MS;

        if (msUntilRefresh > 0) {
            this.refreshTimer = setTimeout(() => {
                this.refreshToken().catch(err => {
                    console.error('Token refresh failed:', err);
                });
            }, msUntilRefresh);
        } else if (this.isLoggedIn()) {
            // Token is expiring soon, refresh now
            this.refreshToken().catch(err => {
                console.error('Token refresh failed:', err);
            });
        }
    },

    // ========================================================================
    // UI Integration
    // ========================================================================

    /**
     * Show the login modal
     */
    showLoginModal() {
        const modal = document.getElementById('login-modal');
        if (modal) {
            modal.classList.add('active');
            modal.setAttribute('aria-hidden', 'false');
            const usernameInput = document.getElementById('login-username');
            if (usernameInput) {
                usernameInput.focus();
            }
        }
    },

    /**
     * Hide the login modal
     */
    hideLoginModal() {
        const modal = document.getElementById('login-modal');
        if (modal) {
            modal.classList.remove('active');
            modal.setAttribute('aria-hidden', 'true');
        }
        // Clear form
        const form = document.getElementById('login-form');
        if (form) {
            form.reset();
        }
        const errorDiv = document.getElementById('login-error');
        if (errorDiv) {
            errorDiv.style.display = 'none';
            errorDiv.textContent = '';
        }
    },

    /**
     * Handle 401 authentication errors
     * @param {Response} response - The fetch response
     */
    handleAuthError(response) {
        if (response.status === 401) {
            this.clearToken();
            this.updateUI();
            this.showLoginModal();
        }
    },

    /**
     * Update UI based on authentication state
     */
    updateUI() {
        const userMenu = document.getElementById('user-menu');
        const userName = document.getElementById('user-name');

        if (this.isLoggedIn()) {
            const username = this.getUsername();
            if (userMenu) {
                userMenu.style.display = 'flex';
            }
            if (userName) {
                userName.textContent = username || 'User';
            }
        } else {
            if (userMenu) {
                userMenu.style.display = 'none';
            }
        }
    },

    // ========================================================================
    // Initialization
    // ========================================================================

    /**
     * Initialize the authentication manager
     */
    init() {
        // Set up login form handler
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();

                const username = document.getElementById('login-username').value;
                const password = document.getElementById('login-password').value;
                const errorDiv = document.getElementById('login-error');
                const submitBtn = loginForm.querySelector('button[type="submit"]');
                const btnText = submitBtn?.querySelector('.btn-text');
                const btnLoading = submitBtn?.querySelector('.btn-loading');

                // Show loading state
                if (btnText) btnText.style.display = 'none';
                if (btnLoading) btnLoading.style.display = 'inline';
                if (submitBtn) submitBtn.disabled = true;

                try {
                    await this.login(username, password);
                    this.hideLoginModal();
                    // Reload dashboard data after login
                    if (typeof loadDashboard === 'function') {
                        loadDashboard();
                    }
                    // Show success toast
                    if (typeof ToastManager !== 'undefined') {
                        ToastManager.success('Logged in successfully');
                    }
                } catch (error) {
                    if (errorDiv) {
                        errorDiv.textContent = error.message;
                        errorDiv.style.display = 'block';
                    }
                } finally {
                    // Reset button state
                    if (btnText) btnText.style.display = 'inline';
                    if (btnLoading) btnLoading.style.display = 'none';
                    if (submitBtn) submitBtn.disabled = false;
                }
            });
        }

        // Set up logout button handler
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.logout();
                if (typeof ToastManager !== 'undefined') {
                    ToastManager.info('Logged out');
                }
            });
        }

        // Check initial state and update UI
        this.updateUI();

        // Schedule refresh if logged in
        if (this.isLoggedIn()) {
            this.scheduleRefresh();
        } else {
            // Show login modal if not logged in
            this.showLoginModal();
        }
    }
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => AuthManager.init());
} else {
    AuthManager.init();
}

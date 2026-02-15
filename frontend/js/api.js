/**
 * API Utilities
 * Handles all backend API calls
 *
 * PRD-036: Updated to support JWT Bearer token authentication.
 */

// API base URL - change for production
const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api'
    : '/api';


/**
 * Generic fetch wrapper with error handling and JWT authentication
 *
 * PRD-036: Added Bearer token support and 401 handling.
 */
async function apiFetch(endpoint, options = {}) {
    const maxRetries = 2;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

        try {
            // Build headers with Bearer token if available
            const headers = {
                'Content-Type': 'application/json',
                ...options.headers,
            };

            // Add Bearer token if logged in (PRD-036)
            if (typeof AuthManager !== 'undefined' && AuthManager.getToken()) {
                headers['Authorization'] = `Bearer ${AuthManager.getToken()}`;
            }

            const response = await fetch(`${API_BASE}${endpoint}`, {
                ...options,
                headers,
                signal: controller.signal,
            });
            clearTimeout(timeoutId);

            // Handle 401 Unauthorized - trigger login modal (PRD-036)
            if (response.status === 401) {
                if (typeof AuthManager !== 'undefined') {
                    AuthManager.handleAuthError(response);
                }
                throw new Error('Authentication required');
            }

            // Retry on 503 Service Unavailable
            if (response.status === 503 && attempt < maxRetries) {
                console.warn(`API 503 on ${endpoint}, retrying (${attempt + 1}/${maxRetries})...`);
                await new Promise(r => setTimeout(r, 1000 * (attempt + 1)));
                continue;
            }

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);

            // Convert AbortError to a descriptive timeout error
            if (error.name === 'AbortError') {
                const timeoutError = new Error(`Request timeout: ${endpoint}`);
                if (attempt < maxRetries) {
                    console.warn(`Timeout on ${endpoint}, retrying (${attempt + 1}/${maxRetries})...`);
                    await new Promise(r => setTimeout(r, 1000 * (attempt + 1)));
                    continue;
                }
                console.error('API Error:', timeoutError);
                if (typeof ToastManager !== 'undefined') {
                    ToastManager.error(`Request failed: ${timeoutError.message}`, 'API Error');
                }
                throw timeoutError;
            }

            // Retry on network errors (TypeError from fetch)
            if (error instanceof TypeError && attempt < maxRetries) {
                console.warn(`Network error on ${endpoint}, retrying (${attempt + 1}/${maxRetries})...`);
                await new Promise(r => setTimeout(r, 1000 * (attempt + 1)));
                continue;
            }

            console.error('API Error:', error);

            // Show toast for non-401 errors after retries exhausted
            if (error.message !== 'Authentication required' && typeof ToastManager !== 'undefined') {
                ToastManager.error(`Request failed: ${error.message}`, 'API Error');
            }

            throw error;
        }
    }
}


// ============================================================================
// Dashboard API
// ============================================================================

/**
 * Get Today's View data
 */
async function getTodayView() {
    return apiFetch('/dashboard/today');
}

/**
 * Get all themes with optional filters
 */
async function getThemes(status = null, minConviction = null) {
    let query = '';
    if (status) query += `?status=${status}`;
    if (minConviction !== null) {
        query += query ? `&min_conviction=${minConviction}` : `?min_conviction=${minConviction}`;
    }
    return apiFetch(`/dashboard/themes${query}`);
}

/**
 * Get theme details
 */
async function getThemeDetail(themeId) {
    return apiFetch(`/dashboard/themes/${themeId}`);
}

/**
 * Update theme status
 */
async function updateThemeStatus(themeId, status) {
    return apiFetch(`/dashboard/themes/${themeId}/status?status=${status}`, {
        method: 'POST',
    });
}

/**
 * Get all sources
 */
async function getSources() {
    return apiFetch('/dashboard/sources');
}

/**
 * Get content from a specific source
 */
async function getSourceContent(sourceName, limit = 50, offset = 0) {
    return apiFetch(`/dashboard/sources/${sourceName}?limit=${limit}&offset=${offset}`);
}

/**
 * Get confluence matrix data
 */
async function getConfluenceMatrix(days = 30, minScore = 4) {
    return apiFetch(`/dashboard/matrix?days=${days}&min_score=${minScore}`);
}

/**
 * Get historical data for a theme
 */
async function getHistoricalData(themeId) {
    return apiFetch(`/dashboard/historical/${themeId}`);
}

/**
 * Get dashboard stats
 */
async function getDashboardStats() {
    return apiFetch('/dashboard/stats');
}

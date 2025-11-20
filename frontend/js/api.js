/**
 * API Utilities
 * Handles all backend API calls
 */

// API base URL - change for production
const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api'
    : '/api';


/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
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

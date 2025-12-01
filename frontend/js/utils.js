/**
 * Utility Functions
 * Common helpers for formatting, dates, etc.
 *
 * Security (PRD-015):
 * - sanitizeHTML() function for XSS prevention
 * - Use textContent for text-only fields
 */

/**
 * Sanitize HTML to prevent XSS attacks (PRD-015)
 *
 * Escapes HTML special characters to prevent script injection.
 * Use this when inserting untrusted content into innerHTML.
 *
 * @param {string} str - String to sanitize
 * @returns {string} - HTML-escaped string
 */
function sanitizeHTML(str) {
    if (str === null || str === undefined) return '';
    if (typeof str !== 'string') str = String(str);

    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Format ISO date string to readable format
 */
function formatDate(isoString) {
    if (!isoString) return 'N/A';

    const date = new Date(isoString);
    const now = new Date();
    const diff = now - date;

    // Less than 1 minute
    if (diff < 60000) {
        return 'Just now';
    }

    // Less than 1 hour
    if (diff < 3600000) {
        const mins = Math.floor(diff / 60000);
        return `${mins}m ago`;
    }

    // Less than 24 hours
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}h ago`;
    }

    // Less than 7 days
    if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days}d ago`;
    }

    // Otherwise, show full date
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
}

/**
 * Format full date with time
 */
function formatDateTime(isoString) {
    if (!isoString) return 'N/A';

    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
    });
}

/**
 * Format conviction score (0-1) as qualitative bucket or percentage.
 *
 * Prefers qualitative buckets (Low/Medium/High/Table Pounding) when available
 * to avoid false precision. Falls back to percentage for legacy data.
 *
 * @param {number|object} conviction - Either a raw number (0-1) or object with bucket
 */
function formatConviction(conviction) {
    if (conviction === null || conviction === undefined) return 'N/A';

    // If conviction is an object with bucket, use qualitative label
    if (typeof conviction === 'object' && conviction.bucket) {
        return formatConvictionBucket(conviction.bucket);
    }

    // Legacy: raw number, show as percentage
    if (typeof conviction === 'number') {
        return `${Math.round(conviction * 100)}%`;
    }

    return 'N/A';
}

/**
 * Format conviction bucket to human-readable label
 */
function formatConvictionBucket(bucket) {
    const labels = {
        'low': 'Low Conviction',
        'medium': 'Medium',
        'high': 'High',
        'table_pounding': 'Table Pounding'
    };
    return labels[bucket] || bucket;
}

/**
 * Format score (0-14) for display
 */
function formatScore(score) {
    if (score === null || score === undefined) return 'N/A';
    return `${score}/14`;
}

/**
 * Format core score (0-10) for display
 */
function formatCoreScore(score) {
    if (score === null || score === undefined) return 'N/A';
    return `${score}/10`;
}

/**
 * Get color class for sentiment
 */
function getSentimentClass(sentiment) {
    if (!sentiment) return 'badge-neutral';

    const s = sentiment.toLowerCase();
    if (s === 'bullish') return 'badge-success';
    if (s === 'bearish') return 'badge-danger';
    if (s === 'neutral') return 'badge-neutral';
    return 'badge-info';
}

/**
 * Get color class for conviction level.
 * Handles both qualitative buckets and legacy raw numbers.
 */
function getConvictionClass(conviction) {
    if (conviction === null || conviction === undefined) return '';

    // If conviction is an object with bucket
    if (typeof conviction === 'object' && conviction.bucket) {
        return getConvictionBucketClass(conviction.bucket);
    }

    // Legacy: raw number (0-1)
    if (typeof conviction === 'number') {
        if (conviction >= 0.75) return 'success';
        if (conviction >= 0.5) return 'warning';
        return 'danger';
    }

    return '';
}

/**
 * Get color class for conviction bucket
 */
function getConvictionBucketClass(bucket) {
    const classes = {
        'low': 'danger',           // Red
        'medium': 'warning',       // Yellow
        'high': 'success',         // Green
        'table_pounding': 'primary' // Blue (most confident)
    };
    return classes[bucket] || '';
}

/**
 * Get color class for status
 */
function getStatusClass(status) {
    if (!status) return 'badge-neutral';

    const s = status.toLowerCase();
    if (s === 'active') return 'badge-success';
    if (s === 'acted_upon') return 'badge-info';
    if (s === 'invalidated') return 'badge-danger';
    if (s === 'archived') return 'badge-neutral';
    return 'badge-neutral';
}

/**
 * Get color for pillar score (0, 1, 2)
 */
function getPillarColor(score) {
    if (score === 2) return '#10b981'; // green
    if (score === 1) return '#f59e0b'; // yellow
    return '#ef4444'; // red
}

/**
 * Format tickers as badges (with XSS protection)
 */
function formatTickers(tickers) {
    if (!tickers || tickers.length === 0) return '';

    return tickers.map(ticker =>
        `<span class="badge badge-info">${sanitizeHTML(ticker)}</span>`
    ).join(' ');
}

/**
 * Truncate text to max length
 */
function truncate(text, maxLength = 100) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Show loading spinner
 */
function showLoading(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = '<div class="loading">Loading...</div>';
    }
}

/**
 * Show error message (with XSS protection)
 */
function showError(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠</div><p>${sanitizeHTML(message)}</p></div>`;
    }
}

/**
 * Show empty state (with XSS protection)
 */
function showEmpty(elementId, message = 'No data available') {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = `<div class="empty-state"><div class="empty-state-icon">📊</div><p>${sanitizeHTML(message)}</p></div>`;
    }
}

/**
 * Debounce function for search/filter inputs
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Navigate to page
 */
function navigateTo(page) {
    window.location.href = page;
}

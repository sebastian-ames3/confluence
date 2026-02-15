/**
 * Health Monitoring Manager (PRD-045)
 *
 * Fetches and displays collection pipeline health status in the header.
 * Shows per-source health with visual indicators (green/yellow/red).
 *
 * Features:
 * - Health indicator widget in header
 * - Dropdown with per-source status
 * - Active alerts display
 * - Alert acknowledgment
 */

const HealthManager = {
    // Cache health data
    healthData: null,
    lastFetch: null,
    CACHE_DURATION: 60000, // 1 minute

    /**
     * Initialize health monitoring
     */
    init() {
        this.createHealthWidget();
        this.fetchAndDisplay();

        // Refresh every 2 minutes
        setInterval(() => this.fetchAndDisplay(), 120000);

        // Close dropdown on outside click
        document.addEventListener('click', (e) => {
            const widget = document.getElementById('health-widget');
            const dropdown = document.getElementById('health-dropdown');
            if (widget && dropdown && !widget.contains(e.target)) {
                dropdown.classList.remove('show');
            }
        });

        console.log('HealthManager initialized');
    },

    /**
     * Create the health widget HTML in the header
     */
    createHealthWidget() {
        // Find header actions container
        const headerActions = document.querySelector('.header-actions');
        if (!headerActions) {
            console.warn('Header actions container not found');
            return;
        }

        // Insert health widget before connection status
        const connectionStatus = headerActions.querySelector('.connection-status');

        const widget = document.createElement('div');
        widget.className = 'health-widget';
        widget.id = 'health-widget';
        widget.innerHTML = `
            <button class="health-indicator" id="health-indicator" title="Collection Health">
                <span class="health-dot" id="health-dot"></span>
                <span class="health-label desktop-only">Sources</span>
            </button>
            <div class="health-dropdown" id="health-dropdown">
                <div class="health-dropdown-header">
                    <span class="health-dropdown-title">Source Health</span>
                    <button class="health-refresh-btn" id="health-refresh-btn" title="Refresh">↻</button>
                </div>
                <div class="health-dropdown-content" id="health-dropdown-content">
                    <div class="health-loading">Loading...</div>
                </div>
                <div class="health-alerts-section" id="health-alerts-section" style="display: none;">
                    <div class="health-alerts-header">Active Alerts</div>
                    <div class="health-alerts-list" id="health-alerts-list"></div>
                </div>
            </div>
        `;

        if (connectionStatus) {
            headerActions.insertBefore(widget, connectionStatus);
        } else {
            headerActions.prepend(widget);
        }

        // Add event listeners
        document.getElementById('health-indicator').addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown();
        });

        document.getElementById('health-refresh-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.fetchAndDisplay(true);
        });
    },

    /**
     * Toggle health dropdown visibility
     */
    toggleDropdown() {
        const dropdown = document.getElementById('health-dropdown');
        if (dropdown) {
            dropdown.classList.toggle('show');
        }
    },

    /**
     * Fetch health data and update display
     */
    async fetchAndDisplay(force = false) {
        // Use cache if valid
        if (!force && this.healthData && this.lastFetch &&
            (Date.now() - this.lastFetch) < this.CACHE_DURATION) {
            return;
        }

        try {
            const data = await apiFetch('/health/sources');
            this.healthData = data;
            this.lastFetch = Date.now();
            this.updateDisplay(data);
        } catch (error) {
            console.error('Failed to fetch health data:', error);
            this.updateDisplayError();
        }
    },

    /**
     * Update the health widget display
     */
    updateDisplay(data) {
        // Update indicator dot
        const dot = document.getElementById('health-dot');
        if (dot) {
            dot.className = 'health-dot';
            dot.classList.add(`health-${data.overall_status || 'unknown'}`);
        }

        // Update dropdown content
        const content = document.getElementById('health-dropdown-content');
        if (content) {
            content.innerHTML = this.renderSourcesList(data.sources);
        }

        // Update alerts section
        const alertsSection = document.getElementById('health-alerts-section');
        const alertsList = document.getElementById('health-alerts-list');

        if (data.alerts && data.alerts.length > 0) {
            alertsSection.style.display = 'block';
            alertsList.innerHTML = this.renderAlertsList(data.alerts);
        } else {
            alertsSection.style.display = 'none';
        }
    },

    /**
     * Render sources list HTML
     */
    renderSourcesList(sources) {
        if (!sources || Object.keys(sources).length === 0) {
            return '<div class="health-empty">No sources configured</div>';
        }

        return Object.entries(sources).map(([name, info]) => {
            const statusClass = this.getStatusClass(info.status);
            const statusIcon = this.getStatusIcon(info.status);

            let detailsHtml = `<div class="health-source-meta">Last: ${this.formatTime(info.last_collection)}</div>`;

            if (info.items_24h !== undefined) {
                detailsHtml += `<div class="health-source-meta">${info.items_24h} items (24h)</div>`;
            }

            if (info.transcription) {
                const t = info.transcription;
                if (t.pending > 0 || t.failed > 0) {
                    detailsHtml += `<div class="health-source-meta">Transcripts: ${t.completed} ok, ${t.pending} pending, ${t.failed} failed</div>`;
                }
                if (t.backlog && t.backlog > 0) {
                    detailsHtml += `<div class="health-source-warning">${t.backlog} videos in backlog (>24h)</div>`;
                }
            }

            return `
                <div class="health-source-item ${statusClass}">
                    <div class="health-source-header">
                        <span class="health-source-icon">${statusIcon}</span>
                        <span class="health-source-name">${this.formatSourceName(name)}</span>
                        <span class="health-source-status-badge ${statusClass}">${sanitizeHTML(info.status)}</span>
                    </div>
                    <div class="health-source-details">
                        ${detailsHtml}
                        ${info.message ? `<div class="health-source-message">${sanitizeHTML(info.message)}</div>` : ''}
                    </div>
                </div>
            `;
        }).join('');
    },

    /**
     * Render alerts list HTML
     */
    renderAlertsList(alerts) {
        return alerts.map(alert => `
            <div class="health-alert-item health-alert-${sanitizeHTML(alert.severity)}">
                <div class="health-alert-header">
                    <span class="health-alert-severity">${sanitizeHTML(alert.severity.toUpperCase())}</span>
                    <span class="health-alert-source">${sanitizeHTML(alert.source || 'System')}</span>
                </div>
                <div class="health-alert-message">${sanitizeHTML(alert.message)}</div>
                <div class="health-alert-actions">
                    <button class="health-alert-ack-btn" onclick="HealthManager.acknowledgeAlert(${parseInt(alert.id, 10)})">
                        Acknowledge
                    </button>
                </div>
            </div>
        `).join('');
    },

    /**
     * Acknowledge an alert
     */
    async acknowledgeAlert(alertId) {
        try {
            await apiFetch(`/health/alerts/${alertId}/acknowledge`, {
                method: 'POST'
            });

            // Refresh health data
            this.fetchAndDisplay(true);

            // Show toast notification
            if (typeof showToast === 'function') {
                showToast('Alert acknowledged', 'success');
            }
        } catch (error) {
            console.error('Failed to acknowledge alert:', error);
            if (typeof showToast === 'function') {
                showToast('Failed to acknowledge alert', 'error');
            }
        }
    },

    /**
     * Update display to show error state
     */
    updateDisplayError() {
        const dot = document.getElementById('health-dot');
        if (dot) {
            dot.className = 'health-dot health-unknown';
        }

        const content = document.getElementById('health-dropdown-content');
        if (content) {
            content.innerHTML = '<div class="health-error">Failed to load health status</div>';
        }
    },

    /**
     * Get CSS class for status
     */
    getStatusClass(status) {
        const statusMap = {
            'healthy': 'health-healthy',
            'degraded': 'health-degraded',
            'stale': 'health-stale',
            'critical': 'health-critical',
            'unknown': 'health-unknown'
        };
        return statusMap[status] || 'health-unknown';
    },

    /**
     * Get icon for status
     */
    getStatusIcon(status) {
        const iconMap = {
            'healthy': '✓',
            'degraded': '⚠',
            'stale': '⏳',
            'critical': '✕',
            'unknown': '?'
        };
        return iconMap[status] || '?';
    },

    /**
     * Format source name for display
     */
    formatSourceName(name) {
        const nameMap = {
            'youtube': 'YouTube',
            'discord': 'Discord',
            '42macro': '42 Macro',
            'substack': 'Substack',
            'kt_technical': 'KT Technical'
        };
        return nameMap[name] || name;
    },

    /**
     * Format timestamp for display
     */
    formatTime(isoString) {
        if (!isoString) return 'Never';

        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

        if (diffHours < 1) {
            const diffMins = Math.floor(diffMs / (1000 * 60));
            return `${diffMins}m ago`;
        } else if (diffHours < 24) {
            return `${diffHours}h ago`;
        } else {
            const diffDays = Math.floor(diffHours / 24);
            return `${diffDays}d ago`;
        }
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for auth to initialize first
    setTimeout(() => {
        HealthManager.init();
    }, 500);
});

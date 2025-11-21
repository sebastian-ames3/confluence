/**
 * WebSocket Client for Real-Time Dashboard Updates
 *
 * Handles:
 * - Connection management with auto-reconnect
 * - Real-time event broadcasting
 * - Toast notifications for updates
 */

class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectInterval = 5000; // 5 seconds
        this.heartbeatInterval = null;
        this.listeners = {};
        this.connectionStatus = 'disconnected';
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const wsUrl = `${protocol}//${host}/ws`;

        console.log(`Connecting to WebSocket: ${wsUrl}`);

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.connectionStatus = 'connected';
                this.reconnectAttempts = 0;
                this.updateConnectionIndicator(true);
                this.startHeartbeat();
                this.emit('connected');
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.connectionStatus = 'disconnected';
                this.updateConnectionIndicator(false);
                this.stopHeartbeat();
                this.emit('disconnected');
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.emit('error', error);
            };

        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.attemptReconnect();
        }
    }

    /**
     * Disconnect from WebSocket
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.stopHeartbeat();
    }

    /**
     * Attempt to reconnect with exponential backoff
     */
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnect attempts reached');
            this.emit('max_reconnect_attempts');
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);

        console.log(`Reconnecting in ${delay/1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        setTimeout(() => {
            this.connect();
        }, delay);
    }

    /**
     * Start heartbeat to keep connection alive
     */
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send('ping');
            }
        }, 30000); // Every 30 seconds
    }

    /**
     * Stop heartbeat
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    /**
     * Handle incoming messages
     */
    handleMessage(message) {
        const { type, data, timestamp } = message;

        console.log('WebSocket message:', type, data);

        // Emit event to listeners
        this.emit(type, data, timestamp);

        // Show toast notification
        switch (type) {
            case 'new_analysis':
                this.showToast(
                    `New ${data.source} analysis`,
                    `${data.content_type} - ${data.sentiment} (${data.conviction}/10)`
                );
                break;

            case 'collection_complete':
                this.showToast(
                    `${data.source} collection complete`,
                    `Collected ${data.items_collected} items`
                );
                break;

            case 'confluence_update':
                if (data.meets_threshold) {
                    this.showToast(
                        'High Confluence Alert!',
                        `Score: ${data.total_score}/14 - ${data.themes.join(', ')}`,
                        'success'
                    );
                }
                break;

            case 'theme_update':
                this.showToast(
                    'Theme Updated',
                    `${data.theme_name}: ${data.conviction}/10 (${data.evidence_count} sources)`
                );
                break;

            case 'high_conviction_alert':
                this.showToast(
                    '⚡ High Conviction Alert!',
                    `${data.theme}: ${data.score}/14 (${data.sentiment})`,
                    'success'
                );
                break;
        }
    }

    /**
     * Register event listener
     */
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    /**
     * Emit event to listeners
     */
    emit(event, ...args) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => {
                try {
                    callback(...args);
                } catch (error) {
                    console.error(`Error in ${event} listener:`, error);
                }
            });
        }
    }

    /**
     * Update connection indicator in UI
     */
    updateConnectionIndicator(connected) {
        const indicator = document.getElementById('ws-connection-indicator');
        if (indicator) {
            indicator.className = connected ? 'update-indicator' : 'update-indicator disconnected';
            indicator.title = connected ? 'Real-time updates active' : 'Disconnected';
        }
    }

    /**
     * Show toast notification
     */
    showToast(title, message, type = 'info') {
        // Remove existing toast
        const existing = document.getElementById('ws-toast');
        if (existing) {
            existing.remove();
        }

        // Create toast
        const toast = document.createElement('div');
        toast.id = 'ws-toast';
        toast.className = 'toast';
        toast.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 4px;">${title}</div>
            <div style="font-size: 13px; color: var(--text-secondary);">${message}</div>
        `;

        // Add type styling
        if (type === 'success') {
            toast.style.borderLeft = '3px solid var(--success)';
        } else if (type === 'error') {
            toast.style.borderLeft = '3px solid var(--danger)';
        }

        document.body.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
}

// Global WebSocket client
const wsClient = new WebSocketClient();

// Auto-connect on page load
document.addEventListener('DOMContentLoaded', () => {
    wsClient.connect();

    // Add connection indicator to header (if not exists)
    const header = document.querySelector('.header-content');
    if (header && !document.getElementById('ws-connection-indicator')) {
        const indicator = document.createElement('span');
        indicator.id = 'ws-connection-indicator';
        indicator.className = 'update-indicator disconnected';
        indicator.title = 'Disconnected';
        header.appendChild(indicator);
    }
});

// Reconnect on page visibility change
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && wsClient.connectionStatus === 'disconnected') {
        wsClient.connect();
    }
});

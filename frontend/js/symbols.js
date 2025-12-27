/**
 * Symbols Tab - Symbol-Level Confluence Tracking (PRD-039)
 *
 * Displays tracked symbols with KT Technical and Discord views,
 * confluence scoring, and price level analysis.
 */

class SymbolsManager {
    constructor() {
        this.symbols = [];
        this.selectedSymbol = null;
    }

    /**
     * Initialize the symbols tab
     */
    async init() {
        console.log('[SymbolsManager] Initializing...');
        await this.loadSymbols();
        this.setupEventListeners();
    }

    /**
     * Load all tracked symbols from API
     */
    async loadSymbols() {
        try {
            console.log('[SymbolsManager] Loading symbols...');

            // Use apiFetch for JWT authentication (PRD-036 compatibility)
            const data = await apiFetch('/symbols');
            this.symbols = data.symbols || [];

            console.log(`[SymbolsManager] Loaded ${this.symbols.length} symbols`);

            this.renderSymbolsList();
        } catch (error) {
            console.error('[SymbolsManager] Failed to load symbols:', error);
            this.showError('Failed to load symbols. Please try again.');
        }
    }

    /**
     * Render the symbols list view
     */
    renderSymbolsList() {
        const container = document.getElementById('symbols-list');
        if (!container) {
            console.error('[SymbolsManager] symbols-list container not found');
            return;
        }

        if (this.symbols.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No symbol data available yet.</p>
                    <p class="text-muted">Run data collection to populate symbol analysis.</p>
                </div>
            `;
            return;
        }

        const html = `
            <div class="symbols-grid">
                ${this.symbols.map(symbol => this.renderSymbolCard(symbol)).join('')}
            </div>
        `;

        container.innerHTML = html;

        // Attach click handlers
        this.symbols.forEach(symbol => {
            const card = document.querySelector(`[data-symbol="${symbol.symbol}"]`);
            if (card) {
                card.addEventListener('click', () => this.showSymbolDetail(symbol.symbol));
            }
        });
    }

    /**
     * Render a single symbol card
     */
    renderSymbolCard(symbol) {
        const ktStatus = this.getStatusIndicator(symbol.kt_view?.bias);
        const discordStatus = this.getStatusIndicator(this.getDiscordBias(symbol.discord_view?.quadrant));
        const confluenceClass = this.getConfluenceClass(symbol.confluence?.score);
        const confluenceLabel = this.getConfluenceLabel(symbol.confluence?.score);

        const ktStale = symbol.kt_view?.is_stale;
        const discordStale = symbol.discord_view?.is_stale;

        return `
            <div class="symbol-card glass-card" data-symbol="${symbol.symbol}">
                <div class="symbol-header">
                    <h3>${symbol.symbol}</h3>
                    ${symbol.active_levels_count ? `<span class="level-count">${symbol.active_levels_count} levels</span>` : ''}
                </div>

                <div class="symbol-views">
                    <div class="view-column">
                        <div class="view-label">KT Technical</div>
                        <div class="view-value">
                            ${ktStatus} ${symbol.kt_view?.wave_position || 'N/A'}
                            ${ktStale ? '<span class="stale-indicator" title="Data is stale">⚠️</span>' : ''}
                        </div>
                        ${symbol.kt_view?.wave_phase ? `<div class="view-meta">${symbol.kt_view.wave_phase}</div>` : ''}
                    </div>

                    <div class="view-column">
                        <div class="view-label">Discord</div>
                        <div class="view-value">
                            ${discordStatus} ${symbol.discord_view?.quadrant || 'N/A'}
                            ${discordStale ? '<span class="stale-indicator" title="Data is stale">⚠️</span>' : ''}
                        </div>
                        ${symbol.discord_view?.iv_regime ? `<div class="view-meta">IV: ${symbol.discord_view.iv_regime}</div>` : ''}
                    </div>
                </div>

                <div class="symbol-confluence ${confluenceClass}">
                    <span class="confluence-label">${confluenceLabel}</span>
                    ${symbol.confluence?.score !== null && symbol.confluence?.score !== undefined
                        ? `<span class="confluence-score">${(symbol.confluence.score * 100).toFixed(0)}%</span>`
                        : '<span class="confluence-score">N/A</span>'}
                </div>

                ${symbol.kt_view?.last_updated || symbol.discord_view?.last_updated
                    ? `<div class="symbol-updated">
                        ${symbol.kt_view?.last_updated
                            ? `KT: ${this.formatDate(symbol.kt_view.last_updated)}`
                            : ''}
                        ${symbol.discord_view?.last_updated
                            ? `Discord: ${this.formatDate(symbol.discord_view.last_updated)}`
                            : ''}
                       </div>`
                    : ''}
            </div>
        `;
    }

    /**
     * Show detailed view for a symbol
     */
    async showSymbolDetail(symbolTicker) {
        try {
            console.log(`[SymbolsManager] Loading detail for ${symbolTicker}`);

            // Use apiFetch for JWT authentication (PRD-036 compatibility)
            const data = await apiFetch(`/symbols/${symbolTicker}`);
            this.selectedSymbol = data;

            this.renderSymbolDetail(data);
        } catch (error) {
            console.error(`[SymbolsManager] Failed to load ${symbolTicker}:`, error);
            this.showError(`Failed to load ${symbolTicker} details.`);
        }
    }

    /**
     * Render the symbol detail modal/view
     */
    renderSymbolDetail(symbol) {
        const modal = document.getElementById('symbol-detail-modal');
        if (!modal) {
            console.error('[SymbolsManager] symbol-detail-modal not found');
            return;
        }

        const content = document.getElementById('symbol-detail-content');
        if (!content) {
            console.error('[SymbolsManager] symbol-detail-content not found');
            return;
        }

        const kt = symbol.kt_technical || {};
        const discord = symbol.discord_options || {};
        const confluence = symbol.confluence || {};
        const levels = symbol.levels || [];

        content.innerHTML = `
            <h2>${symbol.symbol}</h2>

            <div class="detail-grid">
                <div class="detail-section">
                    <h3>KT Technical</h3>
                    <div class="detail-content">
                        ${kt.kt_is_stale ? '<div class="alert alert-warning">⚠️ Data is stale - no update in 14+ days</div>' : ''}
                        ${kt.wave_position ? `<p><strong>Wave:</strong> ${kt.wave_position} (${kt.wave_direction || 'N/A'})</p>` : ''}
                        ${kt.wave_phase ? `<p><strong>Phase:</strong> ${kt.wave_phase}</p>` : ''}
                        ${kt.wave_degree ? `<p><strong>Degree:</strong> ${kt.wave_degree}</p>` : ''}
                        ${kt.bias ? `<p><strong>Bias:</strong> <span class="bias-${kt.bias}">${kt.bias}</span></p>` : ''}
                        ${kt.primary_target ? `<p><strong>Target:</strong> ${kt.primary_target}</p>` : ''}
                        ${kt.primary_support ? `<p><strong>Support:</strong> ${kt.primary_support}</p>` : ''}
                        ${kt.invalidation ? `<p><strong>Invalidation:</strong> ${kt.invalidation}</p>` : ''}
                        ${kt.notes ? `<p class="notes">${kt.notes}</p>` : ''}
                        ${kt.last_updated ? `<p class="text-muted"><small>Updated: ${this.formatDate(kt.last_updated)}</small></p>` : ''}
                    </div>
                </div>

                <div class="detail-section">
                    <h3>Discord Options</h3>
                    <div class="detail-content">
                        ${discord.discord_is_stale ? '<div class="alert alert-warning">⚠️ Data is stale</div>' : ''}
                        ${discord.quadrant ? `<p><strong>Quadrant:</strong> ${discord.quadrant}</p>` : ''}
                        ${discord.iv_regime ? `<p><strong>IV Regime:</strong> ${discord.iv_regime}</p>` : ''}
                        ${discord.strategy_rec ? `<p><strong>Strategy:</strong> ${discord.strategy_rec}</p>` : ''}
                        ${discord.notes ? `<p class="notes">${discord.notes}</p>` : ''}
                        ${discord.last_updated ? `<p class="text-muted"><small>Updated: ${this.formatDate(discord.last_updated)}</small></p>` : ''}
                    </div>
                </div>
            </div>

            ${levels.length > 0 ? this.renderLevelsTable(levels) : '<p class="text-muted">No price levels available.</p>'}

            ${confluence.summary || confluence.trade_setup ? `
                <div class="confluence-section">
                    <h3>Confluence Analysis</h3>
                    ${confluence.score !== null && confluence.score !== undefined
                        ? `<p><strong>Score:</strong> ${(confluence.score * 100).toFixed(0)}% ${confluence.aligned ? '✅ Aligned' : '⚠️ Not Aligned'}</p>`
                        : ''}
                    ${confluence.summary ? `<p>${confluence.summary}</p>` : ''}
                    ${confluence.trade_setup ? `
                        <div class="trade-setup">
                            <h4>Suggested Setup</h4>
                            <p>${confluence.trade_setup}</p>
                        </div>
                    ` : ''}
                </div>
            ` : ''}
        `;

        modal.classList.add('active');
    }

    /**
     * Render the price levels table
     */
    renderLevelsTable(levels) {
        // Sort levels by price descending
        const sorted = [...levels].sort((a, b) => b.price - a.price);

        return `
            <div class="levels-section">
                <h3>Price Levels</h3>
                <table class="levels-table">
                    <thead>
                        <tr>
                            <th>Price</th>
                            <th>Type</th>
                            <th>Direction</th>
                            <th>Source</th>
                            <th>Context</th>
                            <th>Confidence</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${sorted.map(level => `
                            <tr class="${level.is_stale ? 'level-stale' : ''}" ${level.confidence < 0.7 ? 'data-low-confidence="true"' : ''}>
                                <td class="level-price">
                                    ${level.price}${level.price_upper ? `-${level.price_upper}` : ''}
                                    ${level.fib_level ? `<span class="fib-label">${level.fib_level}</span>` : ''}
                                </td>
                                <td><span class="level-type level-type-${level.type}">${level.type}</span></td>
                                <td><span class="direction-${level.direction}">${level.direction || 'N/A'}</span></td>
                                <td>${level.source}</td>
                                <td class="context-snippet" title="${level.context_snippet || ''}">${level.context_snippet || 'N/A'}</td>
                                <td>
                                    ${level.confidence !== null && level.confidence !== undefined
                                        ? `${(level.confidence * 100).toFixed(0)}%${level.confidence < 0.7 ? ' ⚠️' : ''}`
                                        : 'N/A'}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Close modal
        const closeBtn = document.getElementById('close-symbol-detail');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                const modal = document.getElementById('symbol-detail-modal');
                if (modal) modal.classList.remove('active');
            });
        }

        // Close modal on outside click
        const modal = document.getElementById('symbol-detail-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
        }
    }

    /**
     * Get status indicator emoji for bias
     */
    getStatusIndicator(bias) {
        switch (bias?.toLowerCase()) {
            case 'bullish':
                return '🟢';
            case 'bearish':
                return '🔴';
            case 'neutral':
                return '🟡';
            default:
                return '⚪';
        }
    }

    /**
     * Get bias from Discord quadrant
     */
    getDiscordBias(quadrant) {
        if (!quadrant) return null;
        if (quadrant.includes('buy_call') || quadrant.includes('sell_put')) return 'bullish';
        if (quadrant.includes('buy_put') || quadrant.includes('sell_call')) return 'bearish';
        return 'neutral';
    }

    /**
     * Get confluence CSS class
     */
    getConfluenceClass(score) {
        if (score === null || score === undefined) return 'confluence-none';
        if (score >= 0.8) return 'confluence-high';
        if (score >= 0.5) return 'confluence-medium';
        return 'confluence-low';
    }

    /**
     * Get confluence label
     */
    getConfluenceLabel(score) {
        if (score === null || score === undefined) return 'No Data';
        if (score >= 0.8) return 'High Confluence';
        if (score >= 0.5) return 'Medium Confluence';
        return 'Low Confluence';
    }

    /**
     * Format date for display
     */
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    }

    /**
     * Show error message
     */
    showError(message) {
        const container = document.getElementById('symbols-list');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-error">
                    <p>${message}</p>
                </div>
            `;
        }
    }
}

// Export for use in main.js
window.SymbolsManager = SymbolsManager;

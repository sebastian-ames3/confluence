/**
 * Synthesis Quality Manager (PRD-044)
 *
 * Manages quality score display and visualization.
 * Shows synthesis grades, criterion scores, and quality trends.
 */

const QualityManager = {
    // Cache quality data
    qualityData: null,
    trendsData: null,

    /**
     * Initialize quality display
     */
    init() {
        // Listen for synthesis updates to refresh quality display
        document.addEventListener('synthesisLoaded', () => {
            this.loadLatestQuality();
        });

        console.log('QualityManager initialized');
    },

    /**
     * Load and display latest quality score
     */
    async loadLatestQuality() {
        try {
            const data = await apiFetch('/quality/latest');

            if (data.status === 'not_found') {
                this.hideQualityWidget();
                return;
            }

            this.qualityData = data;
            this.renderQualityWidget(data);
        } catch (error) {
            console.error('Failed to load quality data:', error);
            this.hideQualityWidget();
        }
    },

    /**
     * Load quality for a specific synthesis
     */
    async loadQualityForSynthesis(synthesisId) {
        try {
            const data = await apiFetch(`/quality/${synthesisId}`);
            return data;
        } catch (error) {
            console.error(`Failed to load quality for synthesis ${synthesisId}:`, error);
            return null;
        }
    },

    /**
     * Load quality trends
     */
    async loadTrends(days = 30) {
        try {
            const data = await apiFetch(`/quality/trends?days=${days}`);
            this.trendsData = data;
            return data;
        } catch (error) {
            console.error('Failed to load quality trends:', error);
            return null;
        }
    },

    /**
     * Render quality widget in dashboard
     */
    renderQualityWidget(data) {
        // Find or create the quality widget container
        let widget = document.getElementById('quality-widget');

        if (!widget) {
            // Create widget if it doesn't exist
            const container = document.querySelector('.dashboard-grid') ||
                              document.querySelector('.overview-container');
            if (!container) return;

            widget = document.createElement('div');
            widget.id = 'quality-widget';
            widget.className = 'quality-widget glass-card';
            container.appendChild(widget);
        }

        widget.style.display = 'block';
        widget.innerHTML = this.buildWidgetHTML(data);

        // Add event listeners
        this.attachEventListeners();
    },

    /**
     * Build quality widget HTML
     */
    buildWidgetHTML(data) {
        const gradeClass = this.getGradeClass(data.grade);
        const criterionScores = data.criterion_scores || {};

        return `
            <div class="quality-header">
                <h3 class="quality-title">Synthesis Quality</h3>
                <button class="quality-expand-btn" id="quality-expand-btn" title="View details">
                    <span class="expand-icon">+</span>
                </button>
            </div>

            <div class="quality-summary">
                <div class="quality-grade-container">
                    <span class="quality-grade ${gradeClass}">${data.grade}</span>
                    <span class="quality-score">${data.quality_score}/100</span>
                </div>
                ${this.renderFlagsIndicator(data.flags)}
            </div>

            <div class="quality-criteria" id="quality-criteria">
                ${this.renderCriterionBars(criterionScores)}
            </div>

            <div class="quality-details" id="quality-details" style="display: none;">
                ${this.renderFlagsSection(data.flags)}
                ${this.renderSuggestionsSection(data.prompt_suggestions)}
            </div>
        `;
    },

    /**
     * Render criterion score bars
     */
    renderCriterionBars(scores) {
        const criteria = [
            { key: 'confluence_detection', label: 'Confluence', weight: '20%' },
            { key: 'evidence_preservation', label: 'Evidence', weight: '15%' },
            { key: 'source_attribution', label: 'Attribution', weight: '15%' },
            { key: 'youtube_channel_granularity', label: 'YT Channels', weight: '15%' },
            { key: 'nuance_retention', label: 'Nuance', weight: '15%' },
            { key: 'actionability', label: 'Actionable', weight: '10%' },
            { key: 'theme_continuity', label: 'Continuity', weight: '10%' }
        ];

        return criteria.map(c => {
            const score = scores[c.key] || 0;
            const pct = (score / 3) * 100;
            const scoreClass = this.getScoreClass(score);

            return `
                <div class="criterion-row">
                    <div class="criterion-label">
                        <span class="criterion-name">${c.label}</span>
                        <span class="criterion-weight">${c.weight}</span>
                    </div>
                    <div class="criterion-bar-container">
                        <div class="criterion-bar ${scoreClass}" style="width: ${pct}%"></div>
                    </div>
                    <span class="criterion-score">${score}/3</span>
                </div>
            `;
        }).join('');
    },

    /**
     * Render flags indicator
     */
    renderFlagsIndicator(flags) {
        if (!flags || flags.length === 0) {
            return '<span class="quality-flags-ok">No issues</span>';
        }

        return `<span class="quality-flags-warning">${flags.length} issue${flags.length > 1 ? 's' : ''}</span>`;
    },

    /**
     * Render flags section
     */
    renderFlagsSection(flags) {
        if (!flags || flags.length === 0) {
            return '';
        }

        const flagsHtml = flags.map(flag => `
            <div class="quality-flag-item">
                <span class="flag-criterion">${flag.criterion}</span>
                <span class="flag-score">Score: ${flag.score}/3</span>
                <p class="flag-detail">${flag.detail}</p>
            </div>
        `).join('');

        return `
            <div class="quality-flags-section">
                <h4 class="quality-section-title">Issues Found</h4>
                ${flagsHtml}
            </div>
        `;
    },

    /**
     * Render suggestions section
     */
    renderSuggestionsSection(suggestions) {
        if (!suggestions || suggestions.length === 0) {
            return '';
        }

        const suggestionsHtml = suggestions.map(s => `
            <li class="quality-suggestion-item">${s}</li>
        `).join('');

        return `
            <div class="quality-suggestions-section">
                <h4 class="quality-section-title">Improvement Suggestions</h4>
                <ul class="quality-suggestions-list">
                    ${suggestionsHtml}
                </ul>
            </div>
        `;
    },

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        const expandBtn = document.getElementById('quality-expand-btn');
        if (expandBtn) {
            expandBtn.addEventListener('click', () => this.toggleDetails());
        }
    },

    /**
     * Toggle details visibility
     */
    toggleDetails() {
        const details = document.getElementById('quality-details');
        const expandBtn = document.getElementById('quality-expand-btn');
        const icon = expandBtn?.querySelector('.expand-icon');

        if (details) {
            const isHidden = details.style.display === 'none';
            details.style.display = isHidden ? 'block' : 'none';
            if (icon) {
                icon.textContent = isHidden ? '-' : '+';
            }
        }
    },

    /**
     * Hide quality widget
     */
    hideQualityWidget() {
        const widget = document.getElementById('quality-widget');
        if (widget) {
            widget.style.display = 'none';
        }
    },

    /**
     * Get CSS class for grade
     */
    getGradeClass(grade) {
        if (!grade) return 'grade-unknown';

        const letter = grade.charAt(0);
        if (letter === 'A') return 'grade-a';
        if (letter === 'B') return 'grade-b';
        if (letter === 'C') return 'grade-c';
        if (letter === 'D') return 'grade-d';
        return 'grade-f';
    },

    /**
     * Get CSS class for criterion score
     */
    getScoreClass(score) {
        if (score === 3) return 'score-excellent';
        if (score === 2) return 'score-acceptable';
        if (score === 1) return 'score-poor';
        return 'score-fail';
    },

    /**
     * Format quality data for display in synthesis detail view
     */
    formatForSynthesisView(quality) {
        if (!quality) return '';

        return `
            <div class="synthesis-quality-inline">
                <span class="quality-badge ${this.getGradeClass(quality.grade)}">
                    ${quality.grade} (${quality.quality_score}/100)
                </span>
                ${quality.flags?.length > 0 ?
                    `<span class="quality-flags-count">${quality.flags.length} issues</span>` : ''}
            </div>
        `;
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait for auth and main dashboard to load
    setTimeout(() => {
        QualityManager.init();
    }, 1000);
});

/**
 * Charts Manager
 * Central module for initializing and managing all chart instances
 */

const ChartsManager = {
  instances: new Map(),
  initialized: false,

  /**
   * Initialize the charts manager
   */
  init() {
    if (this.initialized) return;

    console.log('[Charts] Initializing ChartsManager');
    this.setupLazyLoading();
    this.initialized = true;
  },

  /**
   * Setup lazy loading for charts
   */
  setupLazyLoading() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const chartId = entry.target.dataset.chart;
          this.loadChart(chartId, entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('[data-chart]').forEach(el => observer.observe(el));
  },

  /**
   * Remove skeleton loader and show canvas
   */
  revealChart(chartId) {
    const skeleton = document.getElementById(`skeleton-${chartId}`);
    const canvas = document.getElementById(`${chartId}-canvas`);

    if (skeleton) {
      skeleton.remove();
    }
    if (canvas) {
      canvas.style.display = 'block';
    }
  },

  /**
   * Load a specific chart
   */
  loadChart(chartId, container) {
    const chartType = container.dataset.chartType;
    const canvasId = `${chartId}-canvas`;

    // Create canvas if not exists
    if (!container.querySelector('canvas')) {
      const wrapper = container.querySelector('.chart-canvas-wrapper');
      if (wrapper) {
        const canvas = document.createElement('canvas');
        canvas.id = canvasId;
        wrapper.appendChild(canvas);
      }
    }

    // Initialize chart based on type
    switch (chartType) {
      case 'confluence-radar':
        this.initConfluenceRadar(canvasId);
        break;
      case 'source-donut':
        this.initSourceDonut(canvasId);
        break;
      case 'theme-timeline':
        this.initThemeTimeline(canvasId);
        break;
      case 'sentiment-gauge':
        this.initSentimentGauge(canvasId);
        break;
      case 'conviction-bar':
        this.initConvictionBar(canvasId);
        break;
      case 'confluence-heatmap':
        this.initConfluenceHeatmap(chartId);
        break;
      default:
        console.warn(`[Charts] Unknown chart type: ${chartType}`);
    }
  },

  /**
   * Initialize Confluence Radar
   */
  initConfluenceRadar(canvasId) {
    if (typeof ConfluenceRadarChart === 'undefined') {
      console.warn('[Charts] ConfluenceRadarChart not loaded');
      return;
    }

    const chart = new ConfluenceRadarChart(canvasId);

    // Sample data - replace with API data
    chart.render({
      labels: ['Equities', 'Bonds', 'Commodities', 'FX', 'Crypto', 'Volatility'],
      sources: [
        { name: '42 Macro', values: [80, 60, 70, 50, 30, 65] },
        { name: 'KT Technical', values: [75, 55, 80, 60, 40, 70] },
        { name: 'Discord', values: [70, 50, 65, 45, 60, 55] }
      ]
    });

    this.instances.set(canvasId, chart);
  },

  /**
   * Initialize Source Donut
   */
  initSourceDonut(canvasId) {
    if (typeof SourceDonutChart === 'undefined') {
      console.warn('[Charts] SourceDonutChart not loaded');
      return;
    }

    const chart = new SourceDonutChart(canvasId);

    // Sample data - replace with API data
    chart.render([
      { source: 'Discord', count: 45 },
      { source: '42 Macro', count: 12 },
      { source: 'KT Technical', count: 8 },
      { source: 'YouTube', count: 15 },
      { source: 'Substack', count: 20 }
    ]);

    this.revealChart('source-donut');
    this.instances.set(canvasId, chart);
  },

  /**
   * Initialize Theme Timeline
   */
  initThemeTimeline(canvasId) {
    if (typeof ThemeTimelineChart === 'undefined') {
      console.warn('[Charts] ThemeTimelineChart not loaded');
      return;
    }

    const chart = new ThemeTimelineChart(canvasId);

    // Sample data - replace with API data
    chart.render({
      dates: ['Dec 1', 'Dec 2', 'Dec 3', 'Dec 4', 'Dec 5', 'Dec 6', 'Dec 7'],
      themes: [
        { name: 'Rate Cuts', status: 'active', dataPoints: [60, 65, 70, 75, 80, 82, 85] },
        { name: 'USD Weakness', status: 'emerging', dataPoints: [30, 35, 40, 50, 55, 60, 65] },
        { name: 'Tech Rotation', status: 'evolved', dataPoints: [80, 78, 75, 70, 68, 65, 60] }
      ]
    });

    this.instances.set(canvasId, chart);
  },

  /**
   * Initialize Sentiment Gauge
   */
  initSentimentGauge(canvasId) {
    if (typeof SentimentGaugeChart === 'undefined') {
      console.warn('[Charts] SentimentGaugeChart not loaded');
      return;
    }

    const chart = new SentimentGaugeChart(canvasId);
    chart.render(35, 'Moderately Bullish');
    this.revealChart('sentiment-gauge');
    this.instances.set(canvasId, chart);
  },

  /**
   * Initialize Conviction Bar
   */
  initConvictionBar(canvasId) {
    if (typeof ConvictionBarChart === 'undefined') {
      console.warn('[Charts] ConvictionBarChart not loaded');
      return;
    }

    const chart = new ConvictionBarChart(canvasId);

    // Sample data - replace with API data
    chart.render([
      { label: 'Rate Cuts Q1', value: 85, sentiment: 'bullish' },
      { label: 'USD Decline', value: 72, sentiment: 'bullish' },
      { label: 'Tech Outperform', value: 65, sentiment: 'neutral' },
      { label: 'Vol Expansion', value: 58, sentiment: 'bearish' },
      { label: 'Gold Rally', value: 45, sentiment: 'bullish' }
    ]);

    this.revealChart('conviction-bar');
    this.instances.set(canvasId, chart);
  },

  /**
   * Initialize Confluence Heatmap
   */
  initConfluenceHeatmap(containerId) {
    if (typeof ConfluenceHeatmap === 'undefined') {
      console.warn('[Charts] ConfluenceHeatmap not loaded');
      return;
    }

    // Remove skeleton for heatmap
    this.revealChart('confluence-heatmap');

    const heatmap = new ConfluenceHeatmap(containerId, {
      onCellClick: (data) => {
        console.log('[Charts] Heatmap cell clicked:', data);
        // Could open a detail modal here
      }
    });

    // Sample data - replace with API data
    heatmap.render({
      sources: ['Discord', '42 Macro', 'KT Technical', 'YouTube', 'Substack'],
      themes: ['Rate Cuts', 'USD Weakness', 'Tech Rotation', 'Gold Rally', 'Vol Expansion'],
      matrix: [
        [1, 1, 1, 0, 1],    // Rate Cuts
        [1, 1, 0, -1, 1],   // USD Weakness
        [0, -1, 1, 1, 0],   // Tech Rotation
        [1, 1, 0, 0, 1],    // Gold Rally
        [-1, 1, -1, 0, 0]   // Vol Expansion
      ]
    });

    this.instances.set(containerId, heatmap);
  },

  /**
   * Handle synthesis data update
   */
  handleDataUpdate(data) {
    // Update relevant charts with new data
    console.log('[Charts] Handling data update');

    // Update sentiment gauge if exists
    const sentimentGauge = this.instances.get('sentiment-gauge-canvas');
    if (sentimentGauge && data.sentiment_score !== undefined) {
      sentimentGauge.update(data.sentiment_score, data.sentiment_label);
    }

    // Update source donut if exists
    const sourceDonut = this.instances.get('source-donut-canvas');
    if (sourceDonut && data.source_counts) {
      sourceDonut.update(data.source_counts);
    }
  },

  /**
   * Handle themes data update
   */
  handleThemesUpdate(themes) {
    console.log('[Charts] Handling themes update');

    // Update theme timeline if exists
    const themeTimeline = this.instances.get('theme-timeline-canvas');
    if (themeTimeline && themes.length > 0) {
      // Transform themes data for timeline
      const dates = this.generateDateLabels(7);
      const timelineData = {
        dates,
        themes: themes.slice(0, 5).map(theme => ({
          name: theme.name,
          status: theme.status,
          dataPoints: theme.conviction_history || this.generateSampleConviction()
        }))
      };
      themeTimeline.render(timelineData);
    }
  },

  /**
   * Generate date labels for the last N days
   */
  generateDateLabels(days) {
    const labels = [];
    const today = new Date();
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    }
    return labels;
  },

  /**
   * Generate sample conviction data
   */
  generateSampleConviction() {
    return Array.from({ length: 7 }, () => Math.floor(Math.random() * 60) + 30);
  },

  /**
   * Destroy all chart instances
   */
  destroyAll() {
    this.instances.forEach((chart, id) => {
      if (chart.destroy) chart.destroy();
    });
    this.instances.clear();
  },

  /**
   * Get chart instance by ID
   */
  get(chartId) {
    return this.instances.get(chartId);
  }
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => ChartsManager.init());
} else {
  ChartsManager.init();
}

// Export
window.ChartsManager = ChartsManager;

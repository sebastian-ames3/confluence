/**
 * Theme Lifecycle Timeline Chart
 * Visualizes theme progression over time
 */

class ThemeTimelineChart {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) {
      console.error(`[ThemeTimeline] Canvas #${canvasId} not found`);
      return;
    }

    this.ctx = this.canvas.getContext('2d');
    this.options = {
      animated: true,
      ...options
    };

    this.chart = null;

    // Status colors
    this.statusColors = {
      emerging: '#FBBF24',   // Yellow
      active: '#10B981',     // Green
      evolved: '#60A5FA',    // Blue
      dormant: '#6B7280'     // Gray
    };
  }

  /**
   * Create the timeline chart
   * @param {Object} data - { dates: [], themes: [{ name, status, dataPoints: [] }] }
   */
  render(data) {
    if (this.chart) {
      this.chart.destroy();
    }

    const datasets = data.themes.map((theme, index) => ({
      label: theme.name,
      data: theme.dataPoints,
      borderColor: this.statusColors[theme.status] || ChartTheme.colors.primary,
      backgroundColor: this.hexToRgba(this.statusColors[theme.status] || ChartTheme.colors.primary, 0.1),
      borderWidth: 2,
      fill: true,
      tension: 0.4,
      pointRadius: 3,
      pointHoverRadius: 6,
      pointBackgroundColor: this.statusColors[theme.status] || ChartTheme.colors.primary
    }));

    this.chart = new Chart(this.ctx, {
      type: 'line',
      data: {
        labels: data.dates,
        datasets
      },
      options: {
        ...ChartTheme.getDefaultOptions('line'),
        scales: {
          x: {
            ...ChartTheme.getDefaultOptions('line').scales.x,
            type: 'category',
            title: {
              display: true,
              text: 'Date',
              color: ChartTheme.legend.color
            }
          },
          y: {
            ...ChartTheme.getDefaultOptions('line').scales.y,
            min: 0,
            max: 100,
            title: {
              display: true,
              text: 'Conviction Score',
              color: ChartTheme.legend.color
            }
          }
        },
        plugins: {
          ...ChartTheme.getDefaultOptions('line').plugins,
          tooltip: {
            ...ChartTheme.getDefaultOptions('line').plugins.tooltip,
            callbacks: {
              afterLabel: (context) => {
                const theme = data.themes[context.datasetIndex];
                return `Status: ${theme.status.charAt(0).toUpperCase() + theme.status.slice(1)}`;
              }
            }
          }
        },
        animation: this.options.animated ? {
          duration: 1200,
          easing: 'easeOutQuart'
        } : false
      }
    });

    return this.chart;
  }

  /**
   * Render status distribution bar
   * @param {HTMLElement} container - Container for the status bar
   * @param {Object} counts - { emerging, active, evolved, dormant }
   */
  renderStatusBar(container, counts) {
    const total = Object.values(counts).reduce((a, b) => a + b, 0);
    if (total === 0) return;

    container.innerHTML = `
      <div class="theme-status-bar">
        ${Object.entries(counts).map(([status, count]) => {
          const percentage = (count / total) * 100;
          return `
            <div
              class="theme-status-segment"
              style="width: ${percentage}%; background: ${this.statusColors[status]}"
              data-tooltip="${status}: ${count} themes (${percentage.toFixed(1)}%)"
            ></div>
          `;
        }).join('')}
      </div>
      <div class="theme-status-legend">
        ${Object.entries(counts).map(([status, count]) => `
          <div class="theme-status-item">
            <span class="theme-status-dot" style="background: ${this.statusColors[status]}"></span>
            <span class="theme-status-label">${status}</span>
            <span class="theme-status-count">${count}</span>
          </div>
        `).join('')}
      </div>
    `;
  }

  hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  destroy() {
    if (this.chart) {
      this.chart.destroy();
      this.chart = null;
    }
  }
}

// Export
window.ThemeTimelineChart = ThemeTimelineChart;

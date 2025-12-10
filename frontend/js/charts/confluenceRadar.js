/**
 * Confluence Radar Chart
 * Visualizes source agreement across different themes/areas
 */

class ConfluenceRadarChart {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) {
      console.error(`[ConfluenceRadar] Canvas #${canvasId} not found`);
      return;
    }

    this.ctx = this.canvas.getContext('2d');
    this.options = {
      animated: true,
      showLabels: true,
      ...options
    };

    this.chart = null;
  }

  /**
   * Create the radar chart
   * @param {Object} data - { labels: [], sources: [{ name, values: [] }] }
   */
  render(data) {
    if (this.chart) {
      this.chart.destroy();
    }

    const datasets = data.sources.map((source, index) => ({
      label: source.name,
      data: source.values,
      backgroundColor: this.hexToRgba(ChartTheme.getSourceColor(source.name), 0.2),
      borderColor: ChartTheme.getSourceColor(source.name),
      borderWidth: 2,
      pointBackgroundColor: ChartTheme.getSourceColor(source.name),
      pointBorderColor: '#fff',
      pointBorderWidth: 1,
      pointRadius: 4,
      pointHoverRadius: 6
    }));

    this.chart = new Chart(this.ctx, {
      type: 'radar',
      data: {
        labels: data.labels,
        datasets
      },
      options: {
        ...ChartTheme.getDefaultOptions('radar'),
        scales: {
          r: {
            beginAtZero: true,
            max: 100,
            ticks: {
              stepSize: 20,
              color: ChartTheme.grid.tickColor,
              backdropColor: 'transparent',
              font: {
                size: ChartTheme.fonts.size.xs
              }
            },
            grid: {
              color: ChartTheme.grid.color
            },
            angleLines: {
              color: ChartTheme.grid.color
            },
            pointLabels: {
              color: ChartTheme.legend.color,
              font: {
                size: ChartTheme.fonts.size.sm,
                family: ChartTheme.fonts.family
              }
            }
          }
        },
        plugins: {
          ...ChartTheme.getDefaultOptions('radar').plugins,
          tooltip: {
            ...ChartTheme.getDefaultOptions('radar').plugins.tooltip,
            callbacks: {
              label: (context) => {
                return `${context.dataset.label}: ${context.raw}% conviction`;
              }
            }
          }
        },
        animation: this.options.animated ? {
          duration: 1000,
          easing: 'easeOutQuart'
        } : false
      }
    });

    return this.chart;
  }

  /**
   * Update chart data
   */
  update(data) {
    if (!this.chart) return;

    this.chart.data.labels = data.labels;
    this.chart.data.datasets = data.sources.map((source, index) => ({
      ...this.chart.data.datasets[index],
      label: source.name,
      data: source.values,
      backgroundColor: this.hexToRgba(ChartTheme.getSourceColor(source.name), 0.2),
      borderColor: ChartTheme.getSourceColor(source.name)
    }));

    this.chart.update('active');
  }

  /**
   * Convert hex to rgba
   */
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
window.ConfluenceRadarChart = ConfluenceRadarChart;

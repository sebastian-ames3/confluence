/**
 * Source Contribution Donut Chart
 * Shows relative contribution from each research source
 */

class SourceDonutChart {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) {
      console.error(`[SourceDonut] Canvas #${canvasId} not found`);
      return;
    }

    this.ctx = this.canvas.getContext('2d');
    this.options = {
      animated: true,
      cutout: '70%',
      showCenter: true,
      ...options
    };

    this.chart = null;
    this.currentData = [];
  }

  /**
   * Create the donut chart
   * @param {Array} data - [{ source, count, percentage }]
   */
  render(data) {
    if (this.chart) {
      this.chart.destroy();
    }

    this.currentData = data;
    const total = data.reduce((sum, item) => sum + item.count, 0);

    this.chart = new Chart(this.ctx, {
      type: 'doughnut',
      data: {
        labels: data.map(d => d.source),
        datasets: [{
          data: data.map(d => d.count),
          backgroundColor: data.map(d => ChartTheme.getSourceColor(d.source)),
          borderColor: 'rgba(15, 23, 42, 0.8)',
          borderWidth: 2,
          hoverOffset: 8
        }]
      },
      options: {
        ...ChartTheme.getDefaultOptions('doughnut'),
        cutout: this.options.cutout,
        plugins: {
          ...ChartTheme.getDefaultOptions('doughnut').plugins,
          legend: {
            display: true,
            position: 'right',
            labels: {
              color: ChartTheme.legend.color,
              font: {
                family: ChartTheme.fonts.family,
                size: ChartTheme.fonts.size.sm
              },
              padding: 12,
              usePointStyle: true,
              pointStyle: 'circle'
            }
          },
          tooltip: {
            ...ChartTheme.getDefaultOptions('doughnut').plugins.tooltip,
            callbacks: {
              label: (context) => {
                const item = data[context.dataIndex];
                const percentage = ((item.count / total) * 100).toFixed(1);
                return `${item.source}: ${item.count} items (${percentage}%)`;
              }
            }
          }
        },
        animation: this.options.animated ? {
          animateRotate: true,
          animateScale: true,
          duration: 1000,
          easing: 'easeOutQuart'
        } : false
      },
      plugins: this.options.showCenter ? [this.centerTextPlugin(total)] : []
    });

    return this.chart;
  }

  /**
   * Plugin to show total in center
   */
  centerTextPlugin(total) {
    const self = this;
    return {
      id: 'centerText',
      afterDraw: (chart) => {
        const { ctx, chartArea: { width, height } } = chart;
        ctx.save();

        // Total number
        ctx.font = `bold ${ChartTheme.fonts.size.xl * 2}px ${ChartTheme.fonts.family}`;
        ctx.fillStyle = ChartTheme.tooltip.titleColor;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(total, width / 2, height / 2 - 10);

        // Label
        ctx.font = `${ChartTheme.fonts.size.sm}px ${ChartTheme.fonts.family}`;
        ctx.fillStyle = ChartTheme.legend.color;
        ctx.fillText('Total Items', width / 2, height / 2 + 20);

        ctx.restore();
      }
    };
  }

  /**
   * Update chart data
   */
  update(data) {
    if (!this.chart) return;

    this.currentData = data;
    const total = data.reduce((sum, item) => sum + item.count, 0);

    this.chart.data.labels = data.map(d => d.source);
    this.chart.data.datasets[0].data = data.map(d => d.count);
    this.chart.data.datasets[0].backgroundColor = data.map(d => ChartTheme.getSourceColor(d.source));

    this.chart.update('active');
  }

  destroy() {
    if (this.chart) {
      this.chart.destroy();
      this.chart = null;
    }
  }
}

// Export
window.SourceDonutChart = SourceDonutChart;

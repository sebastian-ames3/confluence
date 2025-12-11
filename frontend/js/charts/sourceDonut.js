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
    this.tooltipEl = null;
  }

  /**
   * Get or create custom tooltip element
   */
  getOrCreateTooltip(chart) {
    let tooltipEl = chart.canvas.parentNode.querySelector('.donut-tooltip');

    if (!tooltipEl) {
      tooltipEl = document.createElement('div');
      tooltipEl.className = 'donut-tooltip';
      tooltipEl.style.cssText = `
        position: absolute;
        background: rgba(30, 41, 59, 0.95);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 8px;
        padding: 10px 14px;
        pointer-events: none;
        font-family: 'Inter', -apple-system, sans-serif;
        font-size: 12px;
        color: #CBD5E1;
        z-index: 1000;
        white-space: nowrap;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        opacity: 0;
        transition: opacity 0.15s ease;
      `;
      chart.canvas.parentNode.appendChild(tooltipEl);
    }

    return tooltipEl;
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
    const self = this;

    // Ensure parent has relative positioning
    this.canvas.parentNode.style.position = 'relative';

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
            enabled: false, // Disable default tooltip
            external: function(context) {
              const { chart, tooltip } = context;
              const tooltipEl = self.getOrCreateTooltip(chart);

              // Hide if no tooltip
              if (tooltip.opacity === 0) {
                tooltipEl.style.opacity = '0';
                return;
              }

              // Get data for hovered segment
              const dataIndex = tooltip.dataPoints?.[0]?.dataIndex;
              if (dataIndex === undefined || !data[dataIndex]) {
                tooltipEl.style.opacity = '0';
                return;
              }

              const item = data[dataIndex];
              const percentage = ((item.count / total) * 100).toFixed(1);
              const color = ChartTheme.getSourceColor(item.source);

              // Build tooltip content
              tooltipEl.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                  <span style="width: 10px; height: 10px; border-radius: 50%; background: ${color};"></span>
                  <span style="font-weight: 600; color: #F8FAFC;">${item.source}</span>
                </div>
                <div>${item.count} items (${percentage}%)</div>
              `;

              // Position to the right of the chart
              const chartArea = chart.chartArea;
              const tooltipWidth = tooltipEl.offsetWidth || 150;
              const tooltipHeight = tooltipEl.offsetHeight || 50;

              // Place tooltip to the right of the donut, vertically centered
              tooltipEl.style.left = (chartArea.right + 15) + 'px';
              tooltipEl.style.top = ((chartArea.top + chartArea.bottom) / 2 - tooltipHeight / 2) + 'px';
              tooltipEl.style.opacity = '1';
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
    // Clean up tooltip
    const tooltipEl = this.canvas?.parentNode?.querySelector('.donut-tooltip');
    if (tooltipEl) {
      tooltipEl.remove();
    }
  }
}

// Export
window.SourceDonutChart = SourceDonutChart;

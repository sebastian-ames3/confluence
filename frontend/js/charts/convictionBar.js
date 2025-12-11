/**
 * Conviction Bar Chart
 * Horizontal bar chart showing conviction levels by source/theme
 */

class ConvictionBarChart {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) {
      console.error(`[ConvictionBar] Canvas #${canvasId} not found`);
      return;
    }

    this.ctx = this.canvas.getContext('2d');
    this.options = {
      animated: true,
      horizontal: true,
      showValues: true,
      ...options
    };

    this.chart = null;
    this.currentData = [];
  }

  /**
   * Get or create custom tooltip element
   */
  getOrCreateTooltip(chart) {
    let tooltipEl = chart.canvas.parentNode.querySelector('.bar-tooltip');

    if (!tooltipEl) {
      tooltipEl = document.createElement('div');
      tooltipEl.className = 'bar-tooltip';
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
   * Create the bar chart
   * @param {Array} data - [{ label, value, sentiment?, source? }]
   */
  render(data) {
    if (this.chart) {
      this.chart.destroy();
    }

    const sortedData = [...data].sort((a, b) => b.value - a.value);
    this.currentData = sortedData;
    const self = this;

    // Ensure parent has relative positioning
    this.canvas.parentNode.style.position = 'relative';

    this.chart = new Chart(this.ctx, {
      type: 'bar',
      data: {
        labels: sortedData.map(d => d.label),
        datasets: [{
          data: sortedData.map(d => d.value),
          backgroundColor: sortedData.map(d => {
            if (d.sentiment) return ChartTheme.getSentimentColor(d.sentiment);
            if (d.source) return ChartTheme.getSourceColor(d.source);
            return this.getConvictionColor(d.value);
          }),
          borderRadius: 6,
          borderSkipped: false,
          barThickness: 24
        }]
      },
      options: {
        ...ChartTheme.getDefaultOptions('bar'),
        indexAxis: this.options.horizontal ? 'y' : 'x',
        plugins: {
          ...ChartTheme.getDefaultOptions('bar').plugins,
          legend: { display: false },
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

              // Get data for hovered bar
              const dataIndex = tooltip.dataPoints?.[0]?.dataIndex;
              if (dataIndex === undefined || !sortedData[dataIndex]) {
                tooltipEl.style.opacity = '0';
                return;
              }

              const item = sortedData[dataIndex];
              const color = item.sentiment
                ? ChartTheme.getSentimentColor(item.sentiment)
                : item.source
                  ? ChartTheme.getSourceColor(item.source)
                  : self.getConvictionColor(item.value);

              // Build tooltip content
              let sentimentHtml = item.sentiment
                ? `<div style="margin-top: 4px; font-size: 11px; color: #94A3B8;">Sentiment: ${item.sentiment}</div>`
                : '';

              tooltipEl.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                  <span style="width: 10px; height: 10px; border-radius: 2px; background: ${color};"></span>
                  <span style="font-weight: 600; color: #F8FAFC;">${item.label}</span>
                </div>
                <div>Conviction: ${item.value}%</div>
                ${sentimentHtml}
              `;

              // Position above the chart
              const chartArea = chart.chartArea;
              const tooltipHeight = tooltipEl.offsetHeight || 60;

              // Center horizontally, position above chart
              tooltipEl.style.left = ((chartArea.left + chartArea.right) / 2 - (tooltipEl.offsetWidth || 100) / 2) + 'px';
              tooltipEl.style.top = (chartArea.top - tooltipHeight - 10) + 'px';
              tooltipEl.style.opacity = '1';
            }
          }
        },
        scales: {
          x: {
            ...ChartTheme.getDefaultOptions('bar').scales.x,
            max: 100,
            grid: {
              display: !this.options.horizontal,
              color: ChartTheme.grid.color
            }
          },
          y: {
            ...ChartTheme.getDefaultOptions('bar').scales.y,
            grid: {
              display: this.options.horizontal,
              color: ChartTheme.grid.color
            }
          }
        },
        animation: this.options.animated ? {
          duration: 1000,
          easing: 'easeOutQuart',
          delay: (context) => context.dataIndex * 50
        } : false
      },
      plugins: this.options.showValues ? [this.valueLabelsPlugin(sortedData)] : []
    });

    return this.chart;
  }

  /**
   * Get color based on conviction level
   */
  getConvictionColor(value) {
    if (value >= 80) return ChartTheme.colors.bullish;
    if (value >= 60) return '#34D399';
    if (value >= 40) return ChartTheme.colors.quaternary;
    if (value >= 20) return '#F87171';
    return ChartTheme.colors.bearish;
  }

  /**
   * Plugin to show value labels on bars
   */
  valueLabelsPlugin(data) {
    const self = this;
    return {
      id: 'valueLabels',
      afterDatasetsDraw: (chart) => {
        const { ctx } = chart;
        ctx.save();

        chart.getDatasetMeta(0).data.forEach((bar, index) => {
          const value = data[index].value;
          ctx.font = `bold ${ChartTheme.fonts.size.sm}px ${ChartTheme.fonts.family}`;
          ctx.fillStyle = ChartTheme.tooltip.titleColor;
          ctx.textAlign = self.options.horizontal ? 'left' : 'center';
          ctx.textBaseline = 'middle';

          if (self.options.horizontal) {
            ctx.fillText(`${value}%`, bar.x + 8, bar.y);
          } else {
            ctx.fillText(`${value}%`, bar.x, bar.y - 10);
          }
        });

        ctx.restore();
      }
    };
  }

  /**
   * Update chart data
   */
  update(data) {
    if (!this.chart) return;

    const sortedData = [...data].sort((a, b) => b.value - a.value);
    this.currentData = sortedData;

    this.chart.data.labels = sortedData.map(d => d.label);
    this.chart.data.datasets[0].data = sortedData.map(d => d.value);
    this.chart.data.datasets[0].backgroundColor = sortedData.map(d => {
      if (d.sentiment) return ChartTheme.getSentimentColor(d.sentiment);
      if (d.source) return ChartTheme.getSourceColor(d.source);
      return this.getConvictionColor(d.value);
    });

    this.chart.update('active');
  }

  destroy() {
    if (this.chart) {
      this.chart.destroy();
      this.chart = null;
    }
    // Clean up tooltip
    const tooltipEl = this.canvas?.parentNode?.querySelector('.bar-tooltip');
    if (tooltipEl) {
      tooltipEl.remove();
    }
  }
}

// Export
window.ConvictionBarChart = ConvictionBarChart;

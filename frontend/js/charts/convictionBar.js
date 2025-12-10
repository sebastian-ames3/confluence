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
   * Create the bar chart
   * @param {Array} data - [{ label, value, sentiment?, source? }]
   */
  render(data) {
    if (this.chart) {
      this.chart.destroy();
    }

    const sortedData = [...data].sort((a, b) => b.value - a.value);
    this.currentData = sortedData;

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
            ...ChartTheme.getDefaultOptions('bar').plugins.tooltip,
            callbacks: {
              label: (context) => {
                const item = sortedData[context.dataIndex];
                let label = `Conviction: ${item.value}%`;
                if (item.sentiment) label += ` | ${item.sentiment}`;
                return label;
              }
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
  }
}

// Export
window.ConvictionBarChart = ConvictionBarChart;

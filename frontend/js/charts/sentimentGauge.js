/**
 * Sentiment Gauge Chart
 * Visual gauge showing overall market sentiment
 */

class SentimentGaugeChart {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) {
      console.error(`[SentimentGauge] Canvas #${canvasId} not found`);
      return;
    }

    this.ctx = this.canvas.getContext('2d');
    this.options = {
      animated: true,
      min: -100,
      max: 100,
      ...options
    };

    this.chart = null;
    this.currentValue = 0;
    this.currentLabel = '';
  }

  /**
   * Create the gauge chart
   * @param {number} value - Sentiment score (-100 to 100)
   * @param {string} label - Current sentiment label
   */
  render(value, label = '') {
    if (this.chart) {
      this.chart.destroy();
    }

    this.currentValue = value;
    this.currentLabel = label;

    // Normalize value to 0-100 for gauge
    const normalizedValue = ((value - this.options.min) / (this.options.max - this.options.min)) * 100;

    this.chart = new Chart(this.ctx, {
      type: 'doughnut',
      data: {
        datasets: [{
          data: [normalizedValue, 100 - normalizedValue],
          backgroundColor: [
            this.getSentimentGradient(value),
            'rgba(255, 255, 255, 0.05)'
          ],
          borderWidth: 0,
          circumference: 180,
          rotation: 270
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '75%',
        plugins: {
          legend: { display: false },
          tooltip: { enabled: false }
        },
        animation: this.options.animated ? {
          animateRotate: true,
          duration: 1500,
          easing: 'easeOutQuart'
        } : false
      },
      plugins: [this.centerPlugin(value, label)]
    });

    return this.chart;
  }

  /**
   * Get gradient color based on sentiment value
   */
  getSentimentGradient(value) {
    if (value >= 50) return ChartTheme.colors.bullish;
    if (value >= 20) return '#34D399';  // Light green
    if (value >= -20) return ChartTheme.colors.neutral;
    if (value >= -50) return '#F87171';  // Light red
    return ChartTheme.colors.bearish;
  }

  /**
   * Get sentiment label
   */
  getSentimentLabel(value) {
    if (value >= 60) return 'Very Bullish';
    if (value >= 30) return 'Bullish';
    if (value >= -30) return 'Neutral';
    if (value >= -60) return 'Bearish';
    return 'Very Bearish';
  }

  /**
   * Plugin to show value in center
   */
  centerPlugin(value, label) {
    const self = this;
    return {
      id: 'centerValue',
      afterDraw: (chart) => {
        const { ctx, chartArea: { width, height } } = chart;
        ctx.save();

        // Value
        const displayValue = value >= 0 ? `+${value}` : `${value}`;
        ctx.font = `bold ${ChartTheme.fonts.size.xl * 2}px ${ChartTheme.fonts.family}`;
        ctx.fillStyle = self.getSentimentGradient(value);
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(displayValue, width / 2, height / 2 + 20);

        // Label
        const sentimentLabel = label || self.getSentimentLabel(value);
        ctx.font = `${ChartTheme.fonts.size.base}px ${ChartTheme.fonts.family}`;
        ctx.fillStyle = ChartTheme.legend.color;
        ctx.fillText(sentimentLabel, width / 2, height / 2 + 50);

        // Min/Max labels
        ctx.font = `${ChartTheme.fonts.size.xs}px ${ChartTheme.fonts.family}`;
        ctx.fillStyle = ChartTheme.grid.tickColor;
        ctx.textAlign = 'left';
        ctx.fillText('Bearish', 20, height - 10);
        ctx.textAlign = 'right';
        ctx.fillText('Bullish', width - 20, height - 10);

        ctx.restore();
      }
    };
  }

  /**
   * Update gauge value
   */
  update(value, label = '') {
    if (!this.chart) return;

    this.currentValue = value;
    this.currentLabel = label;

    const normalizedValue = ((value - this.options.min) / (this.options.max - this.options.min)) * 100;

    this.chart.data.datasets[0].data = [normalizedValue, 100 - normalizedValue];
    this.chart.data.datasets[0].backgroundColor[0] = this.getSentimentGradient(value);

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
window.SentimentGaugeChart = SentimentGaugeChart;

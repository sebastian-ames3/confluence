# PRD-031: Data Visualization & Charts

## Overview
This PRD defines the data visualization system for the Macro Confluence Hub, including interactive charts, confluence visualizations, theme tracking graphics, and source contribution displays. The goal is to transform complex investment research data into intuitive, actionable visual insights.

**Dependencies**: PRD-027 (Design System), PRD-028 (Components), PRD-030 (Animations)

---

## Visualization Requirements

### Key Data to Visualize
1. **Confluence Zones** - Where multiple sources agree
2. **Source Contributions** - Which sources are providing insights
3. **Theme Lifecycle** - Emerging → Active → Evolved → Dormant
4. **Sentiment Distribution** - Bullish/Bearish/Neutral across sources
5. **Conviction Levels** - Strength of recommendations
6. **Time-based Trends** - Research activity over time
7. **Market Regime** - Current market characterization

### Design Principles
1. **Dark-theme optimized** - Charts designed for dark backgrounds
2. **Glassmorphic integration** - Charts in glass containers
3. **Animated entrances** - Charts animate in on load
4. **Interactive tooltips** - Hover for detailed data
5. **Responsive scaling** - Works on all screen sizes
6. **Accessible colors** - WCAG compliant contrast ratios

---

## Task 1: Chart Theme & Configuration

**File**: `frontend/js/chartConfig.js`

```javascript
/**
 * Chart.js Configuration & Theme
 * Unified chart styling for Macro Confluence Hub
 */

const ChartTheme = {
  // Color palette for data series
  colors: {
    primary: '#60A5FA',      // Blue
    secondary: '#A78BFA',     // Purple
    tertiary: '#34D399',      // Green
    quaternary: '#FBBF24',    // Yellow
    quinary: '#F472B6',       // Pink

    // Semantic colors
    bullish: '#10B981',
    bearish: '#EF4444',
    neutral: '#6B7280',

    // Source colors
    discord: '#5865F2',
    macro42: '#F59E0B',
    ktTechnical: '#10B981',
    youtube: '#EF4444',
    substack: '#FF6719',

    // Gradients
    primaryGradient: ['rgba(96, 165, 250, 0.8)', 'rgba(96, 165, 250, 0.1)'],
    secondaryGradient: ['rgba(167, 139, 250, 0.8)', 'rgba(167, 139, 250, 0.1)'],
    bullishGradient: ['rgba(16, 185, 129, 0.8)', 'rgba(16, 185, 129, 0.1)'],
    bearishGradient: ['rgba(239, 68, 68, 0.8)', 'rgba(239, 68, 68, 0.1)']
  },

  // Font configuration
  fonts: {
    family: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    monoFamily: "'JetBrains Mono', 'Fira Code', monospace",
    size: {
      xs: 10,
      sm: 11,
      base: 12,
      lg: 14,
      xl: 16
    }
  },

  // Grid and axis styling
  grid: {
    color: 'rgba(255, 255, 255, 0.06)',
    borderColor: 'rgba(255, 255, 255, 0.1)',
    tickColor: 'rgba(255, 255, 255, 0.5)'
  },

  // Tooltip styling
  tooltip: {
    backgroundColor: 'rgba(30, 41, 59, 0.95)',
    borderColor: 'rgba(255, 255, 255, 0.1)',
    titleColor: '#F8FAFC',
    bodyColor: '#CBD5E1',
    padding: 12,
    cornerRadius: 8,
    borderWidth: 1
  },

  // Legend styling
  legend: {
    color: '#94A3B8',
    hoverColor: '#F8FAFC'
  },

  /**
   * Create gradient for chart backgrounds
   */
  createGradient(ctx, colorStops, direction = 'vertical') {
    const gradient = direction === 'vertical'
      ? ctx.createLinearGradient(0, 0, 0, ctx.canvas.height)
      : ctx.createLinearGradient(0, 0, ctx.canvas.width, 0);

    gradient.addColorStop(0, colorStops[0]);
    gradient.addColorStop(1, colorStops[1]);
    return gradient;
  },

  /**
   * Get default chart options
   */
  getDefaultOptions(type = 'line') {
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          align: 'end',
          labels: {
            color: this.legend.color,
            font: {
              family: this.fonts.family,
              size: this.fonts.size.sm
            },
            padding: 16,
            usePointStyle: true,
            pointStyle: 'circle'
          }
        },
        tooltip: {
          enabled: true,
          backgroundColor: this.tooltip.backgroundColor,
          titleColor: this.tooltip.titleColor,
          bodyColor: this.tooltip.bodyColor,
          borderColor: this.tooltip.borderColor,
          borderWidth: this.tooltip.borderWidth,
          padding: this.tooltip.padding,
          cornerRadius: this.tooltip.cornerRadius,
          titleFont: {
            family: this.fonts.family,
            size: this.fonts.size.base,
            weight: 600
          },
          bodyFont: {
            family: this.fonts.family,
            size: this.fonts.size.sm
          },
          displayColors: true,
          boxPadding: 4
        }
      },
      scales: type === 'radar' || type === 'pie' || type === 'doughnut' ? {} : {
        x: {
          grid: {
            color: this.grid.color,
            drawBorder: false
          },
          ticks: {
            color: this.grid.tickColor,
            font: {
              family: this.fonts.family,
              size: this.fonts.size.xs
            }
          }
        },
        y: {
          grid: {
            color: this.grid.color,
            drawBorder: false
          },
          ticks: {
            color: this.grid.tickColor,
            font: {
              family: this.fonts.family,
              size: this.fonts.size.xs
            }
          }
        }
      },
      animation: {
        duration: 800,
        easing: 'easeOutQuart'
      }
    };
  },

  /**
   * Get source color by name
   */
  getSourceColor(source) {
    const sourceMap = {
      'discord': this.colors.discord,
      'options insight': this.colors.discord,
      '42 macro': this.colors.macro42,
      '42macro': this.colors.macro42,
      'kt technical': this.colors.ktTechnical,
      'kttechnical': this.colors.ktTechnical,
      'youtube': this.colors.youtube,
      'substack': this.colors.substack
    };
    return sourceMap[source.toLowerCase()] || this.colors.primary;
  },

  /**
   * Get sentiment color
   */
  getSentimentColor(sentiment) {
    const sentimentMap = {
      'bullish': this.colors.bullish,
      'bearish': this.colors.bearish,
      'neutral': this.colors.neutral,
      'mixed': this.colors.quaternary
    };
    return sentimentMap[sentiment?.toLowerCase()] || this.colors.neutral;
  }
};

// Register Chart.js defaults
if (typeof Chart !== 'undefined') {
  Chart.defaults.font.family = ChartTheme.fonts.family;
  Chart.defaults.color = ChartTheme.grid.tickColor;
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ChartTheme;
}
```

---

## Task 2: Confluence Radar Chart

**File**: `frontend/js/charts/confluenceRadar.js`

```javascript
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
            ...ChartTheme.tooltip,
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
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ConfluenceRadarChart;
}
```

---

## Task 3: Source Contribution Donut Chart

**File**: `frontend/js/charts/sourceDonut.js`

```javascript
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
  }

  /**
   * Create the donut chart
   * @param {Array} data - [{ source, count, percentage }]
   */
  render(data) {
    if (this.chart) {
      this.chart.destroy();
    }

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
              pointStyle: 'circle',
              generateLabels: (chart) => {
                const original = Chart.overrides.doughnut.plugins.legend.labels.generateLabels;
                const labels = original.call(this, chart);

                labels.forEach((label, i) => {
                  if (data[i]) {
                    label.text = `${data[i].source} (${data[i].count})`;
                  }
                });

                return labels;
              }
            }
          },
          tooltip: {
            ...ChartTheme.tooltip,
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
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SourceDonutChart;
}
```

---

## Task 4: Theme Lifecycle Timeline

**File**: `frontend/js/charts/themeTimeline.js`

```javascript
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
            ...ChartTheme.tooltip,
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
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ThemeTimelineChart;
}
```

---

## Task 5: Sentiment Gauge Chart

**File**: `frontend/js/charts/sentimentGauge.js`

```javascript
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

    // Normalize value to 0-100 for gauge
    const normalizedValue = ((value - this.options.min) / (this.options.max - this.options.min)) * 100;

    // Create gradient based on sentiment spectrum
    const gradient = this.ctx.createLinearGradient(0, 0, this.canvas.width, 0);
    gradient.addColorStop(0, ChartTheme.colors.bearish);
    gradient.addColorStop(0.5, ChartTheme.colors.neutral);
    gradient.addColorStop(1, ChartTheme.colors.bullish);

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
    return {
      id: 'centerValue',
      afterDraw: (chart) => {
        const { ctx, chartArea: { width, height } } = chart;
        ctx.save();

        // Value
        const displayValue = value >= 0 ? `+${value}` : `${value}`;
        ctx.font = `bold ${ChartTheme.fonts.size.xl * 2}px ${ChartTheme.fonts.family}`;
        ctx.fillStyle = this.getSentimentGradient(value);
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(displayValue, width / 2, height / 2 + 20);

        // Label
        const sentimentLabel = label || this.getSentimentLabel(value);
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

    const normalizedValue = ((value - this.options.min) / (this.options.max - this.options.min)) * 100;

    this.chart.data.datasets[0].data = [normalizedValue, 100 - normalizedValue];
    this.chart.data.datasets[0].backgroundColor[0] = this.getSentimentGradient(value);
    this.chart.options.plugins = [this.centerPlugin(value, label)];

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
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SentimentGaugeChart;
}
```

---

## Task 6: Conviction Bar Chart

**File**: `frontend/js/charts/convictionBar.js`

```javascript
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
            ...ChartTheme.tooltip,
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
    return {
      id: 'valueLabels',
      afterDatasetsDraw: (chart) => {
        const { ctx } = chart;
        ctx.save();

        chart.getDatasetMeta(0).data.forEach((bar, index) => {
          const value = data[index].value;
          ctx.font = `bold ${ChartTheme.fonts.size.sm}px ${ChartTheme.fonts.family}`;
          ctx.fillStyle = ChartTheme.tooltip.titleColor;
          ctx.textAlign = this.options.horizontal ? 'left' : 'center';
          ctx.textBaseline = 'middle';

          if (this.options.horizontal) {
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
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ConvictionBarChart;
}
```

---

## Task 7: Confluence Heatmap

**File**: `frontend/js/charts/confluenceHeatmap.js`

```javascript
/**
 * Confluence Heatmap
 * Matrix visualization showing source agreement on themes
 */

class ConfluenceHeatmap {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      console.error(`[ConfluenceHeatmap] Container #${containerId} not found`);
      return;
    }

    this.options = {
      animated: true,
      cellSize: 40,
      ...options
    };
  }

  /**
   * Render the heatmap
   * @param {Object} data - { sources: [], themes: [], matrix: [[]] }
   * Matrix values: -1 (bearish), 0 (neutral/no data), 1 (bullish)
   */
  render(data) {
    const { sources, themes, matrix } = data;

    // Calculate dimensions
    const cellSize = this.options.cellSize;
    const labelWidth = 120;
    const headerHeight = 80;

    this.container.innerHTML = `
      <div class="heatmap-wrapper">
        <!-- Header row with source labels -->
        <div class="heatmap-header" style="padding-left: ${labelWidth}px; height: ${headerHeight}px;">
          ${sources.map(source => `
            <div class="heatmap-source-label" style="width: ${cellSize}px;">
              <span class="heatmap-source-text">${this.getSourceAbbrev(source)}</span>
            </div>
          `).join('')}
        </div>

        <!-- Matrix rows -->
        <div class="heatmap-body">
          ${themes.map((theme, rowIndex) => `
            <div class="heatmap-row" ${this.options.animated ? `style="animation-delay: ${rowIndex * 50}ms"` : ''}>
              <div class="heatmap-theme-label" style="width: ${labelWidth}px;">
                ${theme}
              </div>
              ${sources.map((source, colIndex) => {
                const value = matrix[rowIndex]?.[colIndex] ?? 0;
                return `
                  <div
                    class="heatmap-cell ${this.getCellClass(value)}"
                    style="width: ${cellSize}px; height: ${cellSize}px;"
                    data-source="${source}"
                    data-theme="${theme}"
                    data-value="${value}"
                    title="${source}: ${this.getValueLabel(value)} on ${theme}"
                  >
                    ${this.getCellIcon(value)}
                  </div>
                `;
              }).join('')}
            </div>
          `).join('')}
        </div>

        <!-- Legend -->
        <div class="heatmap-legend">
          <div class="heatmap-legend-item">
            <div class="heatmap-cell-preview cell-bullish"></div>
            <span>Bullish</span>
          </div>
          <div class="heatmap-legend-item">
            <div class="heatmap-cell-preview cell-neutral"></div>
            <span>Neutral/None</span>
          </div>
          <div class="heatmap-legend-item">
            <div class="heatmap-cell-preview cell-bearish"></div>
            <span>Bearish</span>
          </div>
        </div>
      </div>
    `;

    // Add event listeners
    this.container.querySelectorAll('.heatmap-cell').forEach(cell => {
      cell.addEventListener('click', () => this.onCellClick(cell.dataset));
    });
  }

  /**
   * Get abbreviated source name
   */
  getSourceAbbrev(source) {
    const abbrevs = {
      'Discord': 'DIS',
      'Options Insight': 'OI',
      '42 Macro': '42M',
      'KT Technical': 'KT',
      'YouTube': 'YT',
      'Substack': 'SS'
    };
    return abbrevs[source] || source.substring(0, 3).toUpperCase();
  }

  /**
   * Get cell class based on value
   */
  getCellClass(value) {
    if (value > 0) return 'cell-bullish';
    if (value < 0) return 'cell-bearish';
    return 'cell-neutral';
  }

  /**
   * Get value label
   */
  getValueLabel(value) {
    if (value > 0) return 'Bullish';
    if (value < 0) return 'Bearish';
    return 'No stance';
  }

  /**
   * Get cell icon
   */
  getCellIcon(value) {
    if (value > 0) return '↑';
    if (value < 0) return '↓';
    return '−';
  }

  /**
   * Cell click handler
   */
  onCellClick(dataset) {
    if (this.options.onCellClick) {
      this.options.onCellClick(dataset);
    }
  }

  /**
   * Update heatmap data
   */
  update(data) {
    this.render(data);
  }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ConfluenceHeatmap;
}
```

---

## Task 8: Chart Styles CSS

**File**: `frontend/css/charts/_charts.css`

```css
/* ============================================
   Chart & Visualization Styles
   ============================================ */

/* ----- Chart Container ----- */
.chart-container {
  position: relative;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  padding: var(--space-4);
}

.chart-container-sm {
  height: 200px;
}

.chart-container-md {
  height: 300px;
}

.chart-container-lg {
  height: 400px;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.chart-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text-primary);
}

.chart-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
}

.chart-canvas-wrapper {
  position: relative;
  width: 100%;
  height: calc(100% - 60px);
}

/* ----- Chart Loading State ----- */
.chart-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.chart-loading::after {
  content: '';
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-bg-tertiary);
  border-top-color: var(--color-accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* ----- Chart Empty State ----- */
.chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: var(--color-text-tertiary);
  text-align: center;
  padding: var(--space-8);
}

.chart-empty-icon {
  font-size: 48px;
  margin-bottom: var(--space-4);
  opacity: 0.3;
}

.chart-empty-text {
  font-size: var(--text-sm);
}

/* ----- Heatmap Styles ----- */
.heatmap-wrapper {
  overflow-x: auto;
}

.heatmap-header {
  display: flex;
  align-items: flex-end;
}

.heatmap-source-label {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.heatmap-source-text {
  transform: rotate(-45deg);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.heatmap-body {
  display: flex;
  flex-direction: column;
}

.heatmap-row {
  display: flex;
  align-items: center;
  opacity: 0;
  animation: fadeSlideIn var(--duration-normal) var(--ease-out) forwards;
}

@keyframes fadeSlideIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.heatmap-theme-label {
  flex-shrink: 0;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  padding-right: var(--space-3);
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.heatmap-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin: 2px;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: transform var(--duration-fast) var(--ease-out),
              box-shadow var(--duration-fast) var(--ease-out);
}

.heatmap-cell:hover {
  transform: scale(1.1);
  z-index: 1;
}

.cell-bullish {
  background: rgba(16, 185, 129, 0.3);
  color: var(--color-success);
  border: 1px solid rgba(16, 185, 129, 0.5);
}

.cell-bullish:hover {
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
}

.cell-bearish {
  background: rgba(239, 68, 68, 0.3);
  color: var(--color-error);
  border: 1px solid rgba(239, 68, 68, 0.5);
}

.cell-bearish:hover {
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.4);
}

.cell-neutral {
  background: rgba(107, 114, 128, 0.2);
  color: var(--color-text-tertiary);
  border: 1px solid rgba(107, 114, 128, 0.3);
}

.heatmap-legend {
  display: flex;
  gap: var(--space-4);
  justify-content: center;
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border-primary);
}

.heatmap-legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.heatmap-cell-preview {
  width: 16px;
  height: 16px;
  border-radius: var(--radius-xs);
}

/* ----- Theme Status Bar ----- */
.theme-status-bar {
  display: flex;
  height: 8px;
  border-radius: var(--radius-full);
  overflow: hidden;
  background: var(--color-bg-tertiary);
}

.theme-status-segment {
  transition: width var(--duration-slow) var(--ease-out);
}

.theme-status-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-top: var(--space-3);
}

.theme-status-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
}

.theme-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.theme-status-label {
  color: var(--color-text-secondary);
  text-transform: capitalize;
}

.theme-status-count {
  color: var(--color-text-primary);
  font-weight: 600;
}

/* ----- Confluence Meter ----- */
.confluence-meter {
  position: relative;
  height: 24px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.confluence-meter-fill {
  height: 100%;
  border-radius: var(--radius-full);
  background: linear-gradient(90deg, var(--color-warning), var(--color-success));
  transition: width var(--duration-slow) var(--ease-out);
}

.confluence-meter-label {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-primary);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

/* ----- Mini Sparkline ----- */
.sparkline-container {
  width: 80px;
  height: 24px;
}

.sparkline-container canvas {
  width: 100% !important;
  height: 100% !important;
}

/* ----- Responsive Charts ----- */
@media (max-width: 768px) {
  .chart-container {
    padding: var(--space-3);
  }

  .chart-container-lg {
    height: 300px;
  }

  .heatmap-source-label {
    width: 32px !important;
  }

  .heatmap-cell {
    width: 32px !important;
    height: 32px !important;
  }

  .heatmap-theme-label {
    width: 80px !important;
    font-size: var(--text-xs);
  }
}
```

---

## Task 9: Charts Integration Module

**File**: `frontend/js/charts/index.js`

```javascript
/**
 * Charts Integration Module
 * Central module for managing all chart instances
 */

const ChartsManager = {
  instances: new Map(),

  /**
   * Initialize all dashboard charts
   */
  init() {
    console.log('[Charts] Initializing charts manager');

    // Setup intersection observer for lazy loading
    this.setupLazyLoading();

    // Listen for data updates
    document.addEventListener('synthesis:updated', (e) => this.handleDataUpdate(e.detail));
    document.addEventListener('themes:updated', (e) => this.handleThemesUpdate(e.detail));
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
   * Load a specific chart
   */
  loadChart(chartId, container) {
    const chartType = container.dataset.chartType;
    const canvasId = `${chartId}-canvas`;

    // Create canvas if not exists
    if (!container.querySelector('canvas')) {
      const canvas = document.createElement('canvas');
      canvas.id = canvasId;
      container.querySelector('.chart-canvas-wrapper')?.appendChild(canvas);
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
    const chart = new SourceDonutChart(canvasId);

    // Sample data - replace with API data
    chart.render([
      { source: 'Discord', count: 45 },
      { source: '42 Macro', count: 12 },
      { source: 'KT Technical', count: 8 },
      { source: 'YouTube', count: 15 },
      { source: 'Substack', count: 20 }
    ]);

    this.instances.set(canvasId, chart);
  },

  /**
   * Initialize Theme Timeline
   */
  initThemeTimeline(canvasId) {
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
    const chart = new SentimentGaugeChart(canvasId);
    chart.render(35, 'Moderately Bullish');
    this.instances.set(canvasId, chart);
  },

  /**
   * Initialize Conviction Bar
   */
  initConvictionBar(canvasId) {
    const chart = new ConvictionBarChart(canvasId);

    // Sample data - replace with API data
    chart.render([
      { label: 'Rate Cuts Q1', value: 85, sentiment: 'bullish' },
      { label: 'USD Decline', value: 72, sentiment: 'bullish' },
      { label: 'Tech Outperform', value: 65, sentiment: 'neutral' },
      { label: 'Vol Expansion', value: 58, sentiment: 'bearish' },
      { label: 'Gold Rally', value: 45, sentiment: 'bullish' }
    ]);

    this.instances.set(canvasId, chart);
  },

  /**
   * Initialize Confluence Heatmap
   */
  initConfluenceHeatmap(containerId) {
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
    if (themeTimeline) {
      // Transform themes data for timeline
      // ... implementation depends on data structure
    }
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
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ChartsManager;
}
```

---

## Implementation Checklist

### Task 1: Chart Theme & Configuration
- [ ] Create `frontend/js/chartConfig.js`
- [ ] Define color palette
- [ ] Define font configuration
- [ ] Add gradient helpers
- [ ] Add Chart.js defaults

### Task 2: Confluence Radar Chart
- [ ] Create `frontend/js/charts/confluenceRadar.js`
- [ ] Implement radar chart with source overlays
- [ ] Add animation options
- [ ] Add tooltips

### Task 3: Source Contribution Donut
- [ ] Create `frontend/js/charts/sourceDonut.js`
- [ ] Implement donut with center text
- [ ] Add source color mapping
- [ ] Add interactive legend

### Task 4: Theme Lifecycle Timeline
- [ ] Create `frontend/js/charts/themeTimeline.js`
- [ ] Implement line chart with theme data
- [ ] Add status-based coloring
- [ ] Add status bar component

### Task 5: Sentiment Gauge
- [ ] Create `frontend/js/charts/sentimentGauge.js`
- [ ] Implement half-donut gauge
- [ ] Add sentiment coloring
- [ ] Add center value display

### Task 6: Conviction Bar Chart
- [ ] Create `frontend/js/charts/convictionBar.js`
- [ ] Implement horizontal bar chart
- [ ] Add conviction-based coloring
- [ ] Add value labels

### Task 7: Confluence Heatmap
- [ ] Create `frontend/js/charts/confluenceHeatmap.js`
- [ ] Implement matrix visualization
- [ ] Add cell interactions
- [ ] Add legend

### Task 8: Chart Styles CSS
- [ ] Create `frontend/css/charts/_charts.css`
- [ ] Style chart containers
- [ ] Style heatmap components
- [ ] Style loading/empty states
- [ ] Add responsive styles

### Task 9: Charts Integration
- [ ] Create `frontend/js/charts/index.js`
- [ ] Implement lazy loading
- [ ] Add data event handlers
- [ ] Add instance management

---

## Data API Requirements

The charts require the following data from the backend:

```javascript
// Synthesis data for sentiment gauge
GET /api/dashboard/today
{
  sentiment_score: number,      // -100 to 100
  sentiment_label: string,      // e.g., "Bullish"
  source_counts: [
    { source: string, count: number }
  ]
}

// Theme data for timeline and heatmap
GET /api/themes
{
  themes: [
    {
      name: string,
      status: 'emerging' | 'active' | 'evolved' | 'dormant',
      conviction_history: [{ date: string, score: number }],
      source_stances: {
        [source_name]: 'bullish' | 'bearish' | 'neutral'
      }
    }
  ]
}

// Confluence zones for radar
GET /api/synthesis/latest?format=zones
{
  zones: [
    {
      area: string,         // e.g., "Equities"
      sources: [
        { name: string, conviction: number }
      ]
    }
  ]
}
```

/**
 * Chart.js Configuration & Theme
 * Unified chart styling for Macro Confluence Hub
 */

const ChartTheme = {
  colors: {
    primary: '#60A5FA',
    secondary: '#A78BFA',
    tertiary: '#34D399',
    quaternary: '#FBBF24',
    quinary: '#F472B6',

    bullish: '#10B981',
    bearish: '#EF4444',
    neutral: '#6B7280',

    discord: '#5865F2',
    macro42: '#F59E0B',
    ktTechnical: '#10B981',
    youtube: '#EF4444',
    substack: '#FF6719',

    primaryGradient: ['rgba(96, 165, 250, 0.8)', 'rgba(96, 165, 250, 0.1)'],
    secondaryGradient: ['rgba(167, 139, 250, 0.8)', 'rgba(167, 139, 250, 0.1)'],
    bullishGradient: ['rgba(16, 185, 129, 0.8)', 'rgba(16, 185, 129, 0.1)'],
    bearishGradient: ['rgba(239, 68, 68, 0.8)', 'rgba(239, 68, 68, 0.1)']
  },

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

  grid: {
    color: 'rgba(255, 255, 255, 0.06)',
    borderColor: 'rgba(255, 255, 255, 0.1)',
    tickColor: 'rgba(255, 255, 255, 0.5)'
  },

  tooltip: {
    backgroundColor: 'rgba(30, 41, 59, 0.95)',
    borderColor: 'rgba(255, 255, 255, 0.1)',
    titleColor: '#F8FAFC',
    bodyColor: '#CBD5E1',
    padding: 12,
    cornerRadius: 8,
    borderWidth: 1
  },

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
  },

  /**
   * Hex to RGBA helper
   */
  hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
};

// Register Chart.js defaults if available
if (typeof Chart !== 'undefined') {
  Chart.defaults.font.family = ChartTheme.fonts.family;
  Chart.defaults.color = ChartTheme.grid.tickColor;
}

// Export
window.ChartTheme = ChartTheme;

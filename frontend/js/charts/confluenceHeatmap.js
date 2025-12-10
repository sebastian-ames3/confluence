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
window.ConfluenceHeatmap = ConfluenceHeatmap;

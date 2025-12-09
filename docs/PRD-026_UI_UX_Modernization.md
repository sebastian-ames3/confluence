# PRD-026: UI/UX Modernization

## Overview

Transform the Macro Confluence Hub dashboard from a functional but utilitarian interface into a modern, visually appealing, and intuitive research consumption experience. This redesign incorporates glassmorphism, neumorphism, micro-interactions, motion design, and financial dashboard best practices.

**Status**: Proposed
**Priority**: High
**Estimated Scope**: Major redesign

---

## Current State Analysis

### Screenshots Captured
- `design/current-ui/01-desktop-full-page.png` - Full dashboard view
- `design/current-ui/02-desktop-above-fold.png` - Above the fold content
- `design/current-ui/05-themes-tab.png` - Themes section
- `design/current-ui/06-mobile-view.png` - Mobile responsive view

### Current UI Issues

| Issue | Impact | Priority |
|-------|--------|----------|
| Flat, utilitarian design | Low visual appeal, feels dated | High |
| No glassmorphism/neumorphism | Lacks depth and modern polish | High |
| Minimal micro-interactions | Poor user feedback | High |
| No entrance animations | Feels static and lifeless | Medium |
| Basic typography hierarchy | Hard to scan content quickly | Medium |
| No images/visualizations | Text-heavy, harder to digest | High |
| Redundant headers | "Macro Confluence Hub" appears twice | Low |
| No sidebar navigation | Poor information architecture | Medium |
| Cards lack depth | No shadows or hover effects | High |
| No data sparklines/charts | Source status is just numbers | Medium |

### Current Technical Stack
- Vanilla CSS with CSS variables
- No CSS preprocessor
- Vanilla JavaScript (no framework)
- Chart.js available but underutilized
- Mobile-responsive with basic breakpoints

---

## Design Goals

### Primary Goals
1. **Modern Visual Design**: Implement glassmorphism and subtle neumorphism
2. **Fluid Interactions**: Add micro-interactions and motion design
3. **Visual Data**: Incorporate charts, sparklines, and relevant images
4. **Intuitive Navigation**: Improve information architecture
5. **Consistent Design System**: Establish comprehensive component library

### Design Principles
- **Clarity First**: Information should be easy to scan and understand
- **Delightful Interactions**: Every click should feel responsive
- **Visual Hierarchy**: Most important information stands out
- **Accessibility**: WCAG 2.1 AA compliance minimum
- **Performance**: Animations should be smooth (60fps)

---

## Design System Updates

### Color Palette (Enhanced)

```css
:root {
  /* Primary Palette */
  --primary: #3b82f6;
  --primary-light: #60a5fa;
  --primary-dark: #2563eb;
  --primary-glow: rgba(59, 130, 246, 0.4);

  /* Accent Gradient */
  --gradient-primary: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  --gradient-success: linear-gradient(135deg, #10b981 0%, #059669 100%);
  --gradient-warning: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  --gradient-danger: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);

  /* Background Layers */
  --bg-base: #0f0f0f;
  --bg-surface: #1a1a1a;
  --bg-elevated: #252525;
  --bg-glass: rgba(255, 255, 255, 0.05);
  --bg-glass-hover: rgba(255, 255, 255, 0.08);

  /* Text */
  --text-primary: #f5f5f5;
  --text-secondary: #a0a0a0;
  --text-muted: #606060;

  /* Borders & Shadows */
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-medium: rgba(255, 255, 255, 0.12);
  --border-accent: rgba(59, 130, 246, 0.5);

  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.5);
  --shadow-glow: 0 0 20px var(--primary-glow);

  /* Border Radius (More Rounded) */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-full: 9999px;

  /* Transitions */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 400ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-bounce: 500ms cubic-bezier(0.68, -0.55, 0.27, 1.55);
}
```

### Typography Scale

```css
:root {
  /* Font Family */
  --font-display: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Font Sizes (Fluid) */
  --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.8rem);
  --text-sm: clamp(0.8rem, 0.75rem + 0.25vw, 0.875rem);
  --text-base: clamp(0.875rem, 0.8rem + 0.375vw, 1rem);
  --text-lg: clamp(1rem, 0.9rem + 0.5vw, 1.125rem);
  --text-xl: clamp(1.125rem, 1rem + 0.625vw, 1.25rem);
  --text-2xl: clamp(1.25rem, 1.1rem + 0.75vw, 1.5rem);
  --text-3xl: clamp(1.5rem, 1.25rem + 1.25vw, 2rem);
  --text-4xl: clamp(2rem, 1.5rem + 2.5vw, 3rem);
}
```

---

## Component Redesign

### 1. Glassmorphic Cards

Replace flat cards with glassmorphism effect:

```css
.glass-card {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(12px) saturate(150%);
  -webkit-backdrop-filter: blur(12px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  transition: all var(--transition-normal);
}

.glass-card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.12);
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg), var(--shadow-glow);
}
```

### 2. Neumorphic Buttons (Primary Actions)

```css
.btn-neumorphic {
  background: var(--bg-elevated);
  border: none;
  border-radius: var(--radius-md);
  padding: 12px 24px;
  color: var(--text-primary);
  font-weight: 500;
  box-shadow:
    6px 6px 12px rgba(0, 0, 0, 0.4),
    -6px -6px 12px rgba(255, 255, 255, 0.05);
  transition: all var(--transition-normal);
}

.btn-neumorphic:hover {
  box-shadow:
    4px 4px 8px rgba(0, 0, 0, 0.4),
    -4px -4px 8px rgba(255, 255, 255, 0.05);
}

.btn-neumorphic:active {
  box-shadow:
    inset 4px 4px 8px rgba(0, 0, 0, 0.4),
    inset -4px -4px 8px rgba(255, 255, 255, 0.03);
}
```

### 3. Modern Button with Ripple Effect

```css
.btn-modern {
  position: relative;
  overflow: hidden;
  background: var(--gradient-primary);
  border: none;
  border-radius: var(--radius-md);
  padding: 14px 28px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-normal);
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
}

.btn-modern:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.btn-modern:active {
  transform: translateY(0);
}

/* Ripple effect via JS */
.btn-modern .ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.4);
  transform: scale(0);
  animation: ripple 0.6s linear;
}

@keyframes ripple {
  to {
    transform: scale(4);
    opacity: 0;
  }
}
```

### 4. KPI Cards with Sparklines

```css
.kpi-card {
  background: var(--bg-glass);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: all var(--transition-normal);
}

.kpi-card:hover {
  background: var(--bg-glass-hover);
  border-color: var(--border-medium);
  transform: translateY(-2px);
}

.kpi-label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  font-weight: 600;
}

.kpi-value {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.kpi-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-sm);
  padding: 4px 8px;
  border-radius: var(--radius-full);
}

.kpi-trend.positive {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.kpi-trend.negative {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.kpi-sparkline {
  height: 40px;
  margin-top: auto;
}
```

### 5. Theme Tags with Hover Glow

```css
.theme-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--primary-light);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.theme-tag:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: var(--primary);
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);
  transform: scale(1.05);
}

.theme-tag::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 2s ease-in-out infinite;
}
```

### 6. Conviction Bars with Animation

```css
.conviction-bar {
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-full);
  overflow: hidden;
  position: relative;
}

.conviction-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.conviction-fill.high {
  background: var(--gradient-success);
}

.conviction-fill.medium {
  background: var(--gradient-warning);
}

.conviction-fill.low {
  background: var(--gradient-danger);
}

/* Shimmer effect */
.conviction-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent
  );
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  100% { left: 100%; }
}
```

---

## Layout Redesign

### New Information Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│ HEADER (Glassmorphic, sticky)                                       │
│ ┌─────────┐  ┌─────────────────────────────────┐  ┌───────────────┐ │
│ │  Logo   │  │      Global Search              │  │ Connection    │ │
│ │         │  │      ⌘K to search               │  │ Status + Time │ │
│ └─────────┘  └─────────────────────────────────┘  └───────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ HERO SECTION - Executive Summary                               │ │
│  │ • Market Regime Badge (animated)                               │ │
│  │ • Key insight in large text                                    │ │
│  │ • Sentiment indicator visualization                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ KPI Card │ │ KPI Card │ │ KPI Card │ │ KPI Card │              │
│  │ + Spark  │ │ + Spark  │ │ + Spark  │ │ + Spark  │              │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │
│                                                                     │
│  ┌─────────────────────────┐  ┌─────────────────────────────────┐  │
│  │ CONFLUENCE ZONES        │  │ ATTENTION PRIORITIES            │  │
│  │ (with source alignment  │  │ (ranked cards with drag/hover)  │  │
│  │ visualization)          │  │                                 │  │
│  └─────────────────────────┘  └─────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ SOURCE STATUS (Mini cards with live indicators + sparklines) │  │
│  │ [YouTube] [Discord] [Substack] [42Macro] [KT Technical]      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ THEMES CAROUSEL (Horizontal scroll, glassmorphic cards)       │ │
│  │ ← [Theme Card] [Theme Card] [Theme Card] [Theme Card] →       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ ACTIONS BAR (Floating, glassmorphic)                          │ │
│  │ [Analyze] [Generate Synthesis] [Refresh] [Settings]           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Responsive Breakpoints

| Breakpoint | Layout Changes |
|------------|----------------|
| Desktop (>1200px) | Full 4-column grid, horizontal theme carousel |
| Tablet (768-1200px) | 2-column grid, themes as 2x2 grid |
| Mobile (<768px) | Single column, stacked cards, bottom action bar |

---

## Micro-Interactions & Animations

### 1. Page Load Animations

```css
/* Staggered entrance animation */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card {
  animation: fadeInUp 0.5s ease-out forwards;
  opacity: 0;
}

.card:nth-child(1) { animation-delay: 0.1s; }
.card:nth-child(2) { animation-delay: 0.15s; }
.card:nth-child(3) { animation-delay: 0.2s; }
.card:nth-child(4) { animation-delay: 0.25s; }
```

### 2. Live Data Pulse

```css
.live-indicator {
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  position: relative;
}

.live-indicator::before {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid #10b981;
  animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
}

@keyframes ping {
  75%, 100% {
    transform: scale(2);
    opacity: 0;
  }
}
```

### 3. Skeleton Loading States

```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-elevated) 25%,
    rgba(255, 255, 255, 0.1) 50%,
    var(--bg-elevated) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
  border-radius: var(--radius-sm);
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### 4. Toast Notifications

```css
.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: var(--bg-glass);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: var(--shadow-lg);
  animation: slideInRight 0.4s cubic-bezier(0.68, -0.55, 0.27, 1.55);
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.toast.exiting {
  animation: slideOutRight 0.3s ease-in forwards;
}

@keyframes slideOutRight {
  to {
    opacity: 0;
    transform: translateX(100%);
  }
}
```

### 5. Card Hover Effects

```css
/* Glow on hover for important cards */
.card-glow:hover {
  --glow-color: var(--primary-glow);
  box-shadow:
    0 0 0 1px var(--primary),
    0 0 20px var(--glow-color),
    0 0 40px rgba(59, 130, 246, 0.2);
}

/* Tilt effect on hover (requires JS for mouse tracking) */
.card-tilt {
  transform-style: preserve-3d;
  perspective: 1000px;
}
```

### 6. Number Counter Animation

```javascript
// Animate numbers counting up
function animateValue(element, start, end, duration) {
  const range = end - start;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // Ease out cubic
    const value = Math.round(start + range * eased);
    element.textContent = value;

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  requestAnimationFrame(update);
}
```

---

## Visual Enhancements

### 1. Source Badges with Brand Colors

```css
.source-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: 600;
  transition: all var(--transition-normal);
}

.source-badge.youtube {
  background: rgba(255, 0, 0, 0.1);
  border: 1px solid rgba(255, 0, 0, 0.3);
  color: #ff4444;
}

.source-badge.discord {
  background: rgba(88, 101, 242, 0.1);
  border: 1px solid rgba(88, 101, 242, 0.3);
  color: #7289da;
}

.source-badge.substack {
  background: rgba(255, 102, 0, 0.1);
  border: 1px solid rgba(255, 102, 0, 0.3);
  color: #ff6600;
}

.source-badge.macro42 {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #3b82f6;
}

.source-badge.kt-technical {
  background: rgba(234, 179, 8, 0.1);
  border: 1px solid rgba(234, 179, 8, 0.3);
  color: #eab308;
}
```

### 2. Market Regime Visualization

```css
.regime-indicator {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  border-radius: var(--radius-full);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-size: var(--text-sm);
}

.regime-indicator.risk-on {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(34, 197, 94, 0.1));
  border: 1px solid rgba(16, 185, 129, 0.4);
  color: #10b981;
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.2);
}

.regime-indicator.risk-off {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.1));
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #ef4444;
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
}

.regime-indicator.transitioning {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(217, 119, 6, 0.1));
  border: 1px solid rgba(245, 158, 11, 0.4);
  color: #f59e0b;
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 20px rgba(245, 158, 11, 0.2); }
  50% { box-shadow: 0 0 30px rgba(245, 158, 11, 0.4); }
}
```

### 3. Confluence Score Meter

```css
.confluence-meter {
  position: relative;
  height: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.confluence-meter-fill {
  height: 100%;
  border-radius: var(--radius-full);
  background: linear-gradient(90deg, #10b981 0%, #3b82f6 50%, #8b5cf6 100%);
  transition: width 1.5s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.confluence-meter-fill::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: shimmer 2s infinite;
}

.confluence-score {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  font-size: var(--text-sm);
  font-weight: 700;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}
```

---

## Data Visualization

### 1. Source Activity Sparklines

Use Chart.js or a lightweight library like `sparkline.js` to show:
- Content collected over last 7 days
- Analysis completion rates
- Theme mentions over time

### 2. Confluence Heatmap

Visual representation showing:
- Source agreement matrix
- Theme strength across sources
- Time-based confluence patterns

### 3. Theme Evolution Timeline

Interactive visualization showing:
- Theme lifecycle (emerging → active → evolved → dormant)
- Conviction changes over time
- Related themes cluster

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Update CSS variables and design tokens
- [ ] Implement glassmorphic card component
- [ ] Add micro-interaction utilities
- [ ] Update button styles with ripple effects
- [ ] Implement skeleton loading states

### Phase 2: Layout Restructure (Week 2-3)
- [ ] Redesign header with search
- [ ] Create hero/executive summary section
- [ ] Implement new KPI card layout with sparklines
- [ ] Add source status mini-cards
- [ ] Implement horizontal theme carousel

### Phase 3: Animations & Polish (Week 3-4)
- [ ] Add page entrance animations
- [ ] Implement number counter animations
- [ ] Add card hover effects (tilt, glow)
- [ ] Implement toast notification system
- [ ] Add live data pulse indicators

### Phase 4: Data Visualization (Week 4-5)
- [ ] Implement sparklines for KPI cards
- [ ] Create confluence score meter
- [ ] Add theme evolution timeline
- [ ] Implement source activity visualization

### Phase 5: Testing & Refinement (Week 5-6)
- [ ] Cross-browser testing
- [ ] Performance optimization (60fps animations)
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] Mobile responsiveness testing
- [ ] User feedback integration

---

## Accessibility Requirements

### WCAG 2.1 AA Compliance

1. **Color Contrast**: Minimum 4.5:1 for text, 3:1 for large text
2. **Focus Indicators**: Visible focus ring on all interactive elements
3. **Motion Preferences**: Respect `prefers-reduced-motion`
4. **Screen Reader Support**: Proper ARIA labels and roles
5. **Keyboard Navigation**: All functionality accessible via keyboard

```css
/* Focus visible for keyboard navigation */
:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Skip to main content */
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: var(--primary);
  color: white;
  padding: 8px 16px;
  border-radius: 0 0 var(--radius-sm) 0;
  z-index: 100;
  transition: top 0.3s;
}

.skip-link:focus {
  top: 0;
}
```

---

## Performance Considerations

### Animation Performance
- Use `transform` and `opacity` for animations (GPU-accelerated)
- Avoid animating `width`, `height`, `top`, `left`
- Use `will-change` sparingly and only when needed
- Target 60fps for all animations

### CSS Performance
- Use CSS containment for complex layouts
- Minimize repaints with proper layering
- Use `backdrop-filter` judiciously (can be expensive)

### JavaScript Performance
- Debounce scroll and resize handlers
- Use `requestAnimationFrame` for visual updates
- Lazy load non-critical animations
- Use IntersectionObserver for scroll-triggered animations

---

## Files to Create/Modify

### New Files
- `frontend/css/design-system.css` - Design tokens and variables
- `frontend/css/components.css` - Component-specific styles
- `frontend/css/animations.css` - All animation keyframes
- `frontend/js/animations.js` - JavaScript animation utilities
- `frontend/js/ripple.js` - Ripple effect handler

### Files to Modify
- `frontend/css/style.css` - Update existing styles
- `frontend/css/mobile.css` - Update responsive styles
- `frontend/index.html` - Update HTML structure
- `frontend/js/utils.js` - Add animation utilities

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Lighthouse Performance Score | TBD | 90+ |
| Lighthouse Accessibility Score | TBD | 95+ |
| First Contentful Paint | TBD | < 1.5s |
| Animation Frame Rate | N/A | 60fps |
| User Satisfaction (survey) | TBD | 4.5/5 |

---

## Reference Materials

### Design Inspiration
- `design/76d503f9-*.webp` - Siemens Xcelerator dashboard
- `design/50d11bb3-*.avif` - Camp InsightHub
- `design/ihm-plugin-overview.png` - Plugin card layout

### Current UI Screenshots
- `design/current-ui/` - All captured screenshots

---

## Approval

- [ ] Design review
- [ ] Technical review
- [ ] Accessibility review
- [ ] Performance review
- [ ] Final approval

---

*Created: December 2025*
*Author: Claude Code Assistant*

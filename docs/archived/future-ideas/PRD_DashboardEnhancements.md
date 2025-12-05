# PRD: Dashboard Enhancements

**Status:** Planning
**Priority:** High (User Experience)
**Owner:** Sebastian Ames
**Created:** 2025-11-20
**Target:** Post-MVP Enhancement

---

## Executive Summary

Enhance the Confluence Dashboard with mobile-first UX, real-time updates, and improved data visualization to enable fast decision-making on any device.

**Problem:** Current dashboard is basic, not optimized for mobile use, lacks real-time updates, and doesn't effectively surface high-conviction ideas quickly.

**Solution:** Implement responsive mobile-first design, WebSocket real-time updates, improved confluence visualization, and quick-action workflows.

**Impact:**
- Mobile-first experience (Sebastian checks on phone frequently)
- Real-time confluence updates without page refresh
- Faster decision-making with improved data visualization
- <30 min/day reviewing research (vs 2+ hours manually)

---

## Background

### Current State
- Basic dashboard exists with static views
- No mobile optimization (hard to read on phone)
- Manual page refresh required to see new data
- Confluence scores not visually intuitive
- No quick-action workflows for common tasks

### The Problem
1. **Mobile UX:** Hard to use on phone, Sebastian's primary device for quick checks
2. **Real-time:** Must refresh page to see new analysis results
3. **Information Density:** Hard to quickly identify high-conviction ideas
4. **Navigation:** Too many clicks to drill into specific sources or themes
5. **Manual Actions:** No easy way to trigger collections or mark themes as acted upon

### Why This Matters
- Sebastian needs to make fast decisions during market hours
- Mobile is primary interface for quick checks
- Real-time updates critical for timely action
- Clear visualization of confluence = faster conviction building

---

## User Stories

**As Sebastian**, I want to check my phone during market hours and immediately see high-conviction ideas with supporting confluence scores, so I can make quick trading decisions.

**As Sebastian**, I want new analysis results to appear automatically on my dashboard without refreshing, so I always have the latest information.

**As Sebastian**, I want to tap on a theme and see all supporting sources in one view, so I can quickly validate confluence.

**As Sebastian**, I want to mark themes as "acted upon" or "invalidated" with one tap, so I can track which ideas I've executed on.

**As Sebastian**, I want to trigger on-demand data collection from any source with one tap, so I can get fresh data when I need it.

---

## Technical Design

### Architecture

```
Frontend (React) ↔ WebSocket ↔ Backend (FastAPI)
       ↓                            ↓
   LocalStorage              Database (SQLite)
       ↓                            ↓
   ServiceWorker ← Push Notifications (future)
```

### Components to Build

#### 1. Mobile-First Responsive Design

**Current State:** Desktop-focused layout

**Target State:**
- Mobile breakpoint: < 768px (optimized first)
- Tablet breakpoint: 768px - 1024px
- Desktop breakpoint: > 1024px

**Mobile Layout:**
```
┌─────────────────────┐
│ [≡] Confluence      │ ← Hamburger menu, title
├─────────────────────┤
│ ⚡ HIGH CONVICTION  │ ← Collapsible high-priority section
│ • Theme A (9/14)    │
│ • Theme B (8/14)    │
├─────────────────────┤
│ 📊 Active Themes    │ ← Swipeable cards
│ ┌─────────────────┐ │
│ │ Tech Rotation   │ │
│ │ Score: 7/14     │ │
│ │ 3 sources →     │ │
│ └─────────────────┘ │
├─────────────────────┤
│ 📰 Recent Analysis  │ ← Infinite scroll
│ • 42 Macro ATH      │
│ • Discord Imran     │
└─────────────────────┘
```

**Desktop Layout:**
```
┌────────────────────────────────────────────────────────┐
│ [≡] Confluence              [🔄] [⚙️] [@sebastianames] │
├───────────────┬────────────────────────────────────────┤
│ ⚡ HIGH       │ 📊 CONFLUENCE HEATMAP                  │
│ CONVICTION    │ ┌─────────────────────────────────────┐│
│               │ │       Ma Fu Va Po Pr TA Op          ││
│ • Theme A     │ │ SPY    ██ ██ ░░ ██ ██ ██ ░░         ││
│   (9/14) →    │ │ QQQ    ██ ░░ ░░ ░░ ██ ██ ██         ││
│               │ └─────────────────────────────────────┘│
│ • Theme B     │                                        │
│   (8/14) →    │ 📈 THEME STRENGTH OVER TIME           │
│               │ ┌─────────────────────────────────────┐│
├───────────────┤ │ [Line chart: conviction trends]     ││
│ 📂 SOURCES    │ └─────────────────────────────────────┘│
│               ├────────────────────────────────────────┤
│ • 42 Macro    │ 📰 RECENT ANALYSIS (Last 24h)         │
│ • Discord     │ • 42 Macro ATH - Bullish Tech (8/14)  │
│ • KT Tech     │ • Discord Imran - Bearish Vol (7/14)  │
│ • Twitter     │ • KT Technical - SPY Support (6/14)   │
└───────────────┴────────────────────────────────────────┘
```

#### 2. Real-Time Updates (WebSocket)

**Implementation:**

**Backend (FastAPI):**
```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.active_connections.remove(websocket)

# Broadcast when new analysis completes
async def on_analysis_complete(analysis_id: int):
    analysis = get_analysis(analysis_id)
    await manager.broadcast({
        "type": "new_analysis",
        "data": analysis
    })
```

**Frontend (React):**
```javascript
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/ws');

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    switch (message.type) {
      case 'new_analysis':
        // Update dashboard with new analysis
        setAnalyses(prev => [message.data, ...prev]);
        showToast(`New ${message.data.source} analysis available`);
        break;

      case 'confluence_update':
        // Update confluence scores
        updateConfluenceScores(message.data);
        break;

      case 'collection_complete':
        // Show collection status
        showToast(`${message.data.source} collection complete`);
        break;
    }
  };

  return () => ws.close();
}, []);
```

**Events to Broadcast:**
- `new_analysis`: New content analyzed (PDF, transcript, etc.)
- `confluence_update`: Confluence scores recalculated
- `collection_complete`: Data collection finished
- `theme_update`: Theme strength changed
- `high_conviction_alert`: New idea crossed 7/14 threshold

#### 3. Confluence Visualization

**Heatmap Component:**

Display 7-pillar scores across multiple tickers/themes in color-coded grid.

**Color Scheme:**
- 🟩 Green (2/2): Strong signal
- 🟨 Yellow (1/2): Medium signal
- ⬜ Gray (0/2): Weak/no signal

**Interactive Features:**
- Click cell → See supporting evidence from sources
- Hover → Tooltip with reasoning
- Filter by source, time range, asset class

**Implementation:**
```javascript
const ConfluenceHeatmap = ({ themes }) => {
  const pillars = ['Macro', 'Fundamentals', 'Valuation', 'Positioning',
                   'Policy', 'Price Action', 'Options/Vol'];

  return (
    <div className="heatmap">
      <table>
        <thead>
          <tr>
            <th>Theme</th>
            {pillars.map(p => <th key={p}>{p}</th>)}
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          {themes.map(theme => (
            <tr key={theme.id}>
              <td>{theme.name}</td>
              {pillars.map((pillar, i) => {
                const score = theme.pillar_scores[i];
                const color = score === 2 ? 'green' : score === 1 ? 'yellow' : 'gray';
                return (
                  <td
                    key={pillar}
                    className={`score-${color}`}
                    onClick={() => showEvidence(theme, pillar)}
                  >
                    {score}/2
                  </td>
                );
              })}
              <td className="total">{theme.total_score}/14</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

#### 4. Theme Strength Over Time

**Line Chart Visualization:**

Track how conviction in a theme evolves over time (Bayesian updating).

**Implementation:**
```javascript
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

const ThemeStrengthChart = ({ theme_id }) => {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetch(`/api/themes/${theme_id}/history`)
      .then(res => res.json())
      .then(data => setHistory(data));
  }, [theme_id]);

  return (
    <LineChart width={600} height={300} data={history}>
      <XAxis dataKey="date" />
      <YAxis domain={[0, 14]} />
      <Tooltip />
      <Line
        type="monotone"
        dataKey="total_score"
        stroke="#10b981"
        strokeWidth={2}
      />
    </LineChart>
  );
};
```

**Data Structure:**
```json
[
  {"date": "2025-11-15", "total_score": 5},
  {"date": "2025-11-17", "total_score": 7},
  {"date": "2025-11-19", "total_score": 9},
  {"date": "2025-11-20", "total_score": 8}
]
```

#### 5. Quick Actions

**Manual Collection Trigger:**

```javascript
const TriggerCollection = ({ source }) => {
  const [loading, setLoading] = useState(false);

  const handleTrigger = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/collect/${source}`, {
        method: 'POST'
      });
      if (response.ok) {
        showToast(`${source} collection started`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <button onClick={handleTrigger} disabled={loading}>
      {loading ? '⏳ Collecting...' : `🔄 Collect ${source}`}
    </button>
  );
};
```

**Mark Theme Action:**

```javascript
const ThemeActions = ({ theme_id }) => {
  const markTheme = async (status) => {
    await fetch(`/api/themes/${theme_id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
      headers: { 'Content-Type': 'application/json' }
    });
    showToast(`Theme marked as ${status}`);
  };

  return (
    <div className="theme-actions">
      <button onClick={() => markTheme('acted_upon')}>
        ✅ Acted Upon
      </button>
      <button onClick={() => markTheme('invalidated')}>
        ❌ Invalidated
      </button>
      <button onClick={() => markTheme('monitoring')}>
        👀 Monitoring
      </button>
    </div>
  );
};
```

#### 6. Source Drill-Down

**Modal View:**

Click on any source → See all recent analysis from that source in modal.

```javascript
const SourceModal = ({ source, isOpen, onClose }) => {
  const [analyses, setAnalyses] = useState([]);

  useEffect(() => {
    if (isOpen) {
      fetch(`/api/sources/${source}/recent?limit=20`)
        .then(res => res.json())
        .then(data => setAnalyses(data));
    }
  }, [isOpen, source]);

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <h2>{source} Recent Analysis</h2>
      <div className="analyses-list">
        {analyses.map(analysis => (
          <AnalysisCard key={analysis.id} analysis={analysis} />
        ))}
      </div>
    </Modal>
  );
};
```

---

## Implementation Plan

### Phase 1: Mobile-First Responsive Design (Day 1-2)
- Convert existing components to responsive grid
- Implement hamburger menu for mobile
- Add swipeable theme cards
- Test on multiple devices (iPhone, Android, tablet)

### Phase 2: Real-Time WebSocket Updates (Day 2-3)
- Implement WebSocket endpoint in FastAPI backend
- Add connection manager for broadcasting
- Build React hooks for WebSocket subscription
- Test real-time updates with mock data
- Add reconnection logic for dropped connections

### Phase 3: Enhanced Visualizations (Day 3-4)
- Build confluence heatmap component
- Implement theme strength line chart
- Add interactive tooltips and drill-downs
- Color-code scores for quick scanning

### Phase 4: Quick Actions & UX Polish (Day 4-5)
- Add manual collection trigger buttons
- Implement theme status marking (acted upon, invalidated)
- Build source drill-down modals
- Add toast notifications for user feedback
- Performance optimization (lazy loading, virtualization)

### Phase 5: Testing & Deployment (Day 5)
- Test on real devices (Sebastian's phone)
- Verify WebSocket stability over 24h
- Load testing with 6 months historical data
- Deploy to Railway

---

## Configuration

### Responsive Breakpoints

```css
/* Mobile first approach */
.dashboard {
  /* Mobile (default) */
  padding: 1rem;
}

@media (min-width: 768px) {
  /* Tablet */
  .dashboard {
    padding: 2rem;
    display: grid;
    grid-template-columns: 250px 1fr;
  }
}

@media (min-width: 1024px) {
  /* Desktop */
  .dashboard {
    padding: 3rem;
    grid-template-columns: 300px 1fr 300px;
  }
}
```

### WebSocket Configuration

```json
{
  "websocket": {
    "enabled": true,
    "reconnect_interval": 5000,
    "max_reconnect_attempts": 10,
    "heartbeat_interval": 30000
  }
}
```

### Frontend Performance

```javascript
{
  "lazy_loading": true,
  "virtual_scrolling": true,
  "debounce_search": 300,
  "cache_ttl": 60000
}
```

---

## Testing Strategy

### Responsive Testing
- **Devices**: iPhone 13/14, Samsung Galaxy S23, iPad, Desktop
- **Browsers**: Chrome, Safari, Firefox
- **Orientations**: Portrait and landscape
- **Verify**: No horizontal scroll, readable text, tappable buttons (44px min)

### WebSocket Testing
- **Connection**: Establish, disconnect, reconnect
- **Latency**: Messages arrive within 1 second
- **Stability**: 24-hour connection test
- **Error Handling**: Network drops, server restarts

### Performance Testing
- **Initial Load**: < 2 seconds on 4G
- **Real-time Update**: < 500ms to render new analysis
- **Historical Data**: Render 6 months of themes without lag
- **Memory**: No memory leaks over 24h session

### User Acceptance Testing
- Sebastian tests on his phone during real market hours
- Verify high-conviction ideas are immediately visible
- Test manual collection triggers
- Confirm theme marking works intuitively

---

## Success Metrics

**Must Have:**
- Mobile viewport works perfectly on Sebastian's phone
- Real-time updates appear within 1 second of analysis completion
- High-conviction ideas (≥7/14) always visible above the fold
- <3 taps to trigger collection or mark theme

**Nice to Have:**
- <2 second initial load time on 4G
- Offline mode with cached data
- Theme search/filter
- Export confluence reports

**Track:**
- Mobile vs desktop usage ratio
- Average time to find high-conviction idea
- Number of manual collections triggered
- WebSocket uptime percentage

---

## Risks & Mitigation

### Risk 1: WebSocket Stability
**Problem:** Dropped connections, reconnection loops
**Mitigation:**
- Exponential backoff on reconnect
- Fallback to polling if WebSocket unavailable
- Connection status indicator in UI
- Automatic reconnection on network change

### Risk 2: Mobile Performance
**Problem:** Dashboard slow on phone, high battery drain
**Mitigation:**
- Virtual scrolling for long lists
- Lazy load images and charts
- Throttle WebSocket messages
- Reduce animations on low-power mode

### Risk 3: Data Overload on Small Screen
**Problem:** Too much information, hard to scan
**Mitigation:**
- Progressive disclosure (collapsible sections)
- High-priority content always visible
- Swipeable cards instead of scrolling
- Clear visual hierarchy with typography

### Risk 4: WebSocket Scaling
**Problem:** Too many concurrent connections to Railway instance
**Mitigation:**
- Connection pooling
- Message batching (don't broadcast every update)
- Debounce rapid updates (max 1 message/second per client)
- Monitor connection count, scale if needed

---

## Cost Analysis

### Development Cost
- **Implementation:** 4-5 days
- **Testing:** 1 day
- **Total:** 5-6 days

### Operational Cost
- **WebSocket bandwidth:** Minimal (~1-2 KB/message, ~100 messages/day)
- **Railway compute:** No additional cost (same instance)
- **Total:** $0/month incremental

### Return on Investment
- **Time saved:** 2+ hours/day → 30 min/day = 1.5 hours saved
- **Better decisions:** Faster access to confluence = more timely trades
- **ROI:** Priceless (enables entire system's value prop)

---

## Future Enhancements

### Phase 2 (Optional)
- **Push Notifications:** Alert when high-conviction idea appears (requires service worker + push API)
- **Dark Mode:** Eye-friendly for night trading sessions
- **Customizable Dashboard:** Drag-and-drop widgets
- **Offline Mode:** Service worker caching for offline access

### Phase 3 (Optional)
- **Voice Interface:** "Alexa, what are today's high-conviction ideas?"
- **Share to Trading Journal:** Export confluence reports to Notion/Evernote
- **Multi-user:** Share dashboard with trading partners
- **Historical Replay:** "Show me what dashboard looked like on Nov 15"

---

## Dependencies

- ✅ Backend API endpoints (exist)
- ✅ Database with confluence scores (exists)
- ✅ React frontend (exists)
- New: WebSocket server (FastAPI WebSocket endpoint)
- New: Mobile-responsive components
- New: Real-time update hooks
- New: Visualization libraries (recharts or chart.js)

---

## UI Component Library

**Recommendation:** Use lightweight, mobile-optimized library

**Options:**
1. **Tailwind CSS + Headless UI** (Recommended)
   - Utility-first, mobile-first by default
   - Tiny bundle size
   - Full control over styling

2. **Chakra UI**
   - Accessible by default
   - Built-in responsive design
   - Slightly heavier bundle

3. **React + Vanilla CSS**
   - Lightest option
   - Most control
   - More implementation work

**Decision:** Start with Tailwind CSS for speed, can optimize later.

---

## Accessibility Considerations

- **WCAG 2.1 AA Compliance:**
  - Color contrast ≥4.5:1 for text
  - Keyboard navigation for all actions
  - Screen reader friendly labels
  - Touch targets ≥44px on mobile

- **Performance Accessibility:**
  - Reduced motion option (respect prefers-reduced-motion)
  - Text scaling support (use rem, not px)
  - Clear focus indicators

---

## Timeline

**Day 1:** Mobile-responsive layout (grid, breakpoints, hamburger menu)
**Day 2:** Real-time WebSocket implementation (backend + frontend)
**Day 3:** Enhanced visualizations (heatmap, line charts)
**Day 4:** Quick actions & UX polish (buttons, modals, notifications)
**Day 5:** Testing on real devices, performance optimization, deploy
**Total:** 5-6 days

---

## Approval Checklist

Before implementing:
- [ ] PRD reviewed and approved
- [ ] Mobile-first approach validated
- [ ] WebSocket architecture agreed upon
- [ ] UI/UX mockups approved (if needed)
- [ ] Performance targets defined

---

**Version:** 1.0
**Last Updated:** 2025-11-20

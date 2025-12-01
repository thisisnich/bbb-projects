# Module 5 Display Demo - Planning Questions

## Clarifying Questions

### 1. Demo Environment
- [ ] **Physical hardware demo?** (Actual BBBW + OLED + Bar Graph + Buttons)
- [ ] **Web-based simulation?** (Show display views in browser)
- [ ] **Both?** (Web sim for easy demo, hardware for final)

### 2. Dashboard Integration
- [ ] **Control panel in dashboard?** (Buttons to switch Module 5 views)
- [ ] **Live preview?** (See what Module 5 is showing in real-time)
- [ ] **Simulate button presses?** (Click buttons in dashboard to change Module 5 view)
- [ ] **Send test data?** (Inject fake data to Module 5 for demo)

### 3. Priority Features for Demo
**What's most important to show?**
- [ ] All 5 OLED views (Status, History, Weather, Alternatives, Info)
- [ ] Button navigation (5 buttons switching views)
- [ ] Bar Graph visualization (hourly pattern)
- [ ] Auto-rotation (cycling through views)
- [ ] Real-time data updates (from Module 1/2/3)
- [ ] Simulated data (for demo without other modules)

### 4. Implementation Approach
**Which approach do you prefer?**

**Option A: Web Simulation (Easiest for Demo)**
- Add Module 5 display panel to existing dashboard
- Simulate OLED screen with HTML/CSS
- Simulate Bar Graph with HTML bars
- Clickable buttons to switch views
- Can demo immediately without hardware

**Option B: Physical Device + Dashboard Control**
- Build actual Module 5 client (BBBW code)
- Dashboard has control panel to send commands
- Dashboard shows what Module 5 is displaying
- Requires hardware setup

**Option C: Hybrid (Recommended)**
- Web simulation in dashboard for easy demo
- Physical device code ready for deployment
- Dashboard can control both

### 5. Data Source
- [ ] **Real data** (from Module 1/2/3 if running)
- [ ] **Simulated data** (fake data for demo)
- [ ] **Both** (toggle between real/simulated)

---

## Suggested Implementation Plan

### Phase 1: Web Simulation in Dashboard (Quick Demo)
1. Add Module 5 display panel to `dashboard.html`
2. Simulate OLED screen (128x64 pixel style)
3. Simulate Bar Graph (8 bars showing hourly pattern)
4. Add 5 buttons (Now, History, Weather, Alt, Info)
5. Show all 5 views with sample data
6. Auto-rotation after 60 seconds idle

### Phase 2: Dashboard Control Panel
1. Add "Module 5 Control" section to dashboard
2. Buttons to manually switch Module 5 views
3. Toggle between real data and simulated data
4. Send commands to Module 5 (if physical device exists)

### Phase 3: Physical Device (If Needed)
1. Create `module5/Module5_Display_Client.py`
2. Receives data from server via SocketIO
3. Controls OLED, Bar Graph, reads buttons
4. Updates display based on button presses
5. Dashboard shows live preview of what Module 5 displays

---

## Quick Start: Web Simulation

**Fastest way to demo Module 5:**

1. **Add to dashboard.html:**
   - Module 5 display panel (simulated OLED)
   - 5 navigation buttons
   - Bar Graph visualization
   - All 5 views with sample data

2. **Add to CloudServer:**
   - `DisplayUpdate` event handler (already exists)
   - Simulate Module 5 data if no real data
   - Send updates to dashboard

3. **Demo features:**
   - Click buttons to switch views
   - Show auto-rotation
   - Show real-time updates (if Module 1 running)
   - Show simulated data (if no modules running)

---

## Questions for You:

1. **Do you need physical hardware for the demo, or is web simulation enough?**
2. **Should the dashboard be able to control Module 5, or just display what it shows?**
3. **What's the priority - quick demo or full implementation?**
4. **Do you have Module 5 hardware ready, or just planning?**

Let me know your answers and I'll implement accordingly! 🚀


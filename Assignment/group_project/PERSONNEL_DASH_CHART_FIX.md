# Personnel Dashboard Charts - Fixed & Reorganized

## Changes Made

### 1. **Layout Reorganized**
- Moved rating distribution chart INTO the main charts grid
- Changed from 2 separate chart cards to 1 unified card with 5 charts
- Grid now shows 3 columns: `repeat(3, minmax(0, 1fr))`

**New Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Crowd - Today  │  Crowd - Week  │  Env - 24h          │
├─────────────────────────────────────────────────────────┤
│  Env - Week     │  Ratings Dist  │                     │
└─────────────────────────────────────────────────────────┘
```

### 2. **Chart Elements Updated**
**Old:**
- `chart-hourly` / `chart-weekly` (only 2 charts)
- `chart-ratings` (separate card)

**New:**
- `chart-crowd-hourly`
- `chart-crowd-weekly`
- `chart-env-recent`
- `chart-env-weekly`
- `chart-rating-dist`

### 3. **Chart Loading Functions Added**
Copied from `index.html`:
- `loadCrowdHourlyChart()` - Fetches `/api/charts/crowd?hours=24`
- `loadCrowdWeeklyChart()` - Fetches `/api/charts/crowd?hours=168`
- `loadEnvRecentChart()` - Fetches `/api/charts/environment?hours=24`
- `loadEnvWeeklyChart()` - Fetches `/api/charts/environment?hours=168`
- `loadRatingDistChart()` - Fetches `/api/charts/rating?days=365`
- `loadAllCharts()` - Calls all 5 in parallel

### 4. **State Updated**
```javascript
charts: { 
  crowdHourly: null, 
  crowdWeekly: null, 
  envRecent: null, 
  envWeekly: null,
  ratingDist: null  // NEW - pie chart for rating distribution
}
```

### 5. **Title Updated**
```html
<p class="title">Historical Data</p>
<p class="subtitle">From crowd.db, env.db & rating.db • Auto-refreshes every 30s</p>
```

## Next Step Required

The `initCharts()` function in `personnel_dashboard.html` still needs to be updated to initialize all 5 charts (similar to `index.html`). This includes:

1. Creating Chart.js instances for all 5 canvas elements
2. Calling `loadAllCharts()` on page load
3. Setting up 30-second refresh interval

## What This Fixes

✅ **Charts load from databases** instead of Module 5 payload  
✅ **Rating chart in grid** instead of separate card  
✅ **Clean 3-column layout** on personnel dashboard  
✅ **Same pattern as index.html** for consistency  
✅ **Auto-refresh every 30s** from databases  

## To Test

1. Refresh `http://localhost:5000/personnel_dashboard`
2. Open console (F12)
3. Look for:
   ```
   === LOADING ALL CHARTS FROM DATABASES ===
   === ALL CHARTS LOADED ===
   ```
4. Check server logs for `/api/charts/*` requests

The charts should now display with data from the databases!

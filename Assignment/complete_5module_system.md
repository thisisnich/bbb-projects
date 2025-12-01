# 🎯 5-MODULE SMART SPORTS FACILITY SYSTEM
## Complete Hardware Specifications & System Architecture

**Target User:** Young adults (19-30) using public sports facilities  
**Problem Solved:** Uncertainty about court availability, wasted trips, poor planning  
**Solution:** Real-time monitoring + cloud analytics + on-site displays

---

## SYSTEM OVERVIEW

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  MODULE 1   │  │  MODULE 2   │  │  MODULE 3   │
│   Crowd     │  │ Environment │  │  Feedback   │
│  Detection  │  │  Monitoring │  │   Kiosk     │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
                   ┌────▼─────┐
                   │  CLOUD   │
                   │Analytics │
                   │  Server  │
                   └────┬─────┘
                        │
       ┌────────────────┼────────────────┐
       │                │                │
  ┌────▼────┐      ┌────▼────┐     ┌────▼────┐
  │MODULE 4 │      │MODULE 5 │     │MODULE 5 │
  │Security │      │Court A  │     │Court B  │
  │ Alert   │      │Display  │     │Display  │
  │Dashboard│      └─────────┘     └─────────┘
  └─────────┘
  
  Residents/Security           Public Users
  Monitor & Respond            Check Before Visit
```

---

# MODULE 1: CROWD INTELLIGENCE UNIT
**"Real-time occupancy monitoring with multi-sensor validation"**

## Hardware Configuration
- **BeagleBone Black Wireless**
- **USB Webcam** (doesn't count toward click limit)
- **Click Boards (4/4):**
  1. **MIC Click** - Audio level detection (ball bouncing, voices)
  2. **Motion Click** - PIR motion sensor for backup detection
  3. **OLED Click** - Local status display (cycles through data)
  4. **Proximity Click** - Detect people approaching court area

## Primary Function
Count people and detect activity level using multi-sensor fusion for high accuracy.

## Multi-Sensor Approach

### Data Sources:
- **Webcam + Google AI:** "I see 8 people on court"
- **MIC Click:** "Noise level is 75dB - active game happening"
- **Motion Click:** "Detected movement in last 30 seconds"
- **Proximity Click:** "People within 2 meters of court boundary"

### Data Fusion Logic:
```python
# All sensors must agree for high confidence
if webcam_count == 8 and noise > 70dB and motion == True:
    confidence = 0.95
    status = "FULL - Active game"
elif webcam_count == 0 and noise < 40dB and motion == False:
    confidence = 0.98
    status = "EMPTY"
else:
    confidence = 0.60
    status = "Validating..."
```

## OLED Display (Cycles every 10 seconds)

**Screen 1: Current Status**
```
┌─────────────────┐
│ COURT A         │
│ ════════════════│
│                 │
│ 🔴 FULL         │
│ 8 people        │
│                 │
│ Conf: 95%       │
└─────────────────┘
```

**Screen 2: Sensor Health**
```
┌─────────────────┐
│ SENSOR STATUS   │
│ ════════════════│
│                 │
│ 📷 Cam:    ✓   │
│ 🔊 Audio:  75dB│
│ 👋 Motion: ✓   │
│ 📏 Prox:   ✓   │
└─────────────────┘
```

**Screen 3: Audio Recording**
```
┌─────────────────┐
│ RECORDING       │
│ ════════════════│
│                 │
│ Audio: 75dB     │
│ Noise level:    │
│ [████████░░]    │
│ (High activity) │
└─────────────────┘
```

## Data Output (every 30 seconds)
```json
{
  "module_id": "crowd_unit_1",
  "court_id": "basketball_a",
  "timestamp": "2025-11-17T15:30:00",
  "people_count": 8,
  "crowd_level": "full",
  "noise_db": 75,
  "motion_detected": true,
  "proximity_triggered": true,
  "confidence": 0.95,
  "sensors_status": {
    "webcam": "ok",
    "mic": "ok", 
    "motion": "ok",
    "proximity": "ok"
  }
}
```

## Why This Combination?
- **Webcam** = Visual count (most accurate)
- **MIC** = Activity level + validates webcam
- **Motion** = Backup if webcam fails/dark
- **Proximity** = Boundary detection, queue forming
- **OLED** = Debug/monitoring for technicians

## Standalone Value
- Facilities manager can monitor occupancy remotely
- Security can verify crowd levels
- Works even if cloud connection fails (local display)
- Audio detection works in poor lighting/night

---

# MODULE 2: ENVIRONMENTAL CONDITIONS STATION
**"Sports-safe weather monitoring with air quality"**

## Hardware Configuration
- **BeagleBone Black Wireless**
- **Click Boards (4/4):**
  1. **Environment Click** - Temp, humidity, pressure, VOC gases (4-in-1!)
  2. **UV 3 Click** - UV index for sunburn risk
  3. **Bar Graph 2 Click** - Visual comfort indicator (LED bars)
  4. **OLED Click** - Local display (cycles through readings)

## Primary Function
Comprehensive environmental monitoring to determine if conditions are safe and comfortable for outdoor sports.

## Sensor Capabilities

### Environment Click Provides:
- **Temperature:** Is it too hot/cold to play?
- **Humidity:** Comfort level assessment
- **Pressure:** Weather change predictions
- **VOC (Volatile Organic Compounds):** Air quality near traffic/pollution

### UV 3 Click:
- **UV Index:** Sunburn risk level (0-11+ scale)

## OLED Display (Cycles every 8 seconds)

**Screen 1: Temperature & Comfort**
```
┌─────────────────┐
│ TEMPERATURE     │
│ ════════════════│
│                 │
│ 🌡️  32°C        │
│                 │
│ Status: HOT ⚠️  │
│ Play: Caution   │
└─────────────────┘
```

**Screen 2: Humidity & Air Quality**
```
┌─────────────────┐
│ AIR CONDITIONS  │
│ ════════════════│
│                 │
│ 💧 Humidity: 78%│
│ 🌫️  VOC: Good   │
│                 │
│ Comfort: Medium │
└─────────────────┘
```

**Screen 3: UV Warning**
```
┌─────────────────┐
│ UV INDEX        │
│ ════════════════│
│                 │
│ ☀️  Level: 9    │
│ Risk: VERY HIGH │
│                 │
│ ⚠️ Sunscreen!   │
└─────────────────┘
```

**Screen 4: Overall Recommendation**
```
┌─────────────────┐
│ PLAY ADVISORY   │
│ ════════════════│
│                 │
│ Safe: YES ✓     │
│ Comfort: 3/5    │
│                 │
│ Best: After 6PM │
└─────────────────┘
```

## Bar Graph 2 Click - Visual Comfort Indicator

At-a-glance LED status (visible from distance):
```
█████ (5 LEDs - Green):  Perfect conditions
████░ (4 LEDs - Green):  Good
███░░ (3 LEDs - Yellow): Okay
██░░░ (2 LEDs - Orange): Caution - hot/humid
█░░░░ (1 LED - Red):     Not recommended - dangerous
```

### Comfort Score Algorithm:
```python
def calculate_comfort_score():
    score = 5.0
    
    # Temperature penalties
    if temp > 35: score -= 2
    elif temp > 32: score -= 1
    elif temp < 15: score -= 1.5
    
    # Humidity penalties  
    if humidity > 80: score -= 1
    elif humidity > 70: score -= 0.5
    
    # UV penalties
    if uv_index > 10: score -= 1
    elif uv_index > 7: score -= 0.5
    
    # VOC/Air quality
    if voc > threshold: score -= 1
    
    return max(1, min(5, score))  # Clamp between 1-5
```

## Data Output
```json
{
  "module_id": "environment_unit_2",
  "timestamp": "2025-11-17T15:30:00",
  "temperature_c": 32,
  "humidity_percent": 78,
  "pressure_hpa": 1013,
  "voc_level": "good",
  "voc_reading": 245,
  "uv_index": 9,
  "comfort_score": 3.0,
  "playable": true,
  "warnings": ["high_uv", "high_heat"],
  "recommendations": [
    "use_sunscreen", 
    "stay_hydrated", 
    "play_after_6pm"
  ]
}
```

## Why This Combination?
- **Environment Click** = 4 sensors in 1 board (efficient!)
- **UV 3** = Critical for outdoor sports safety
- **Bar Graph** = Instant visual indicator from distance
- **OLED** = Detailed readings for those who want specifics

## Standalone Value
- Athletes check safety before traveling
- Parents verify conditions for children
- Coaches make informed decisions about practice
- Prevents heat stroke and UV damage

---

# MODULE 3: INTERACTIVE FEEDBACK KIOSK
**"Community voice with intuitive gesture control"**

## Hardware Configuration
- **BeagleBone Black Wireless**
- **Click Boards (4/4):**
  1. **OLED Click** - Display prompts and feedback
  2. **IR Gesture Click** - Touchless gesture interaction (swipe, select)
  3. **LED Matrix Click** - Visual status/confirmation icons
  4. **Buzz 2 Click** - Audio feedback for interactions

## Primary Function
Collect user feedback through intuitive gesture-based interface. Gather court ratings and maintenance reports.

## User Workflow

### Step 1: Attract Attention
User approaches kiosk → sees pulsing LED pattern

### Step 2: Gesture Interaction
- **Wave** to activate
- **Swipe left/right** to navigate options
- **Push gesture** (toward sensor) to confirm

### Step 3: Confirmation
Visual (LED Matrix) + Audio (Buzz) + Display feedback

## OLED Display States

**Idle Screen:**
```
┌─────────────────────┐
│ RATE THIS COURT     │
│ ═══════════════════ │
│                     │
│     👋              │
│  Wave to start      │
│                     │
│ [LED Matrix shows   │
│  pulsing pattern]   │
└─────────────────────┘
```

**Rating Selection (Swipe to navigate):**
```
┌─────────────────────┐
│ HOW'S THE COURT?    │
│ ═══════════════════ │
│                     │
│   ⭐⭐⭐⭐⭐          │
│   << Perfect! >>    │
│                     │
│ Swipe to change     │
│ Push to confirm ✓   │
└─────────────────────┘
```

**Rating Options (Swipe through):**
- ⭐⭐⭐⭐⭐ Perfect
- ⭐⭐⭐⭐☆ Very Good  
- ⭐⭐⭐☆☆ Good
- ⭐⭐☆☆☆ Fair
- ⭐☆☆☆☆ Poor - Needs Fix

**Confirmation:**
```
┌─────────────────────┐
│ ✓ THANKS!           │
│ ═══════════════════ │
│                     │
│ Your rating: ⭐⭐⭐⭐ │
│                     │
│ [LED Matrix shows   │
│  checkmark pattern] │
│ [Buzz: Beep!]       │
└─────────────────────┘
```

## Maintenance Report Mode

**Activated by:** Swipe down twice (special gesture)

```
┌─────────────────────┐
│ REPORT ISSUE?       │
│ ═══════════════════ │
│                     │
│ Select problem:     │
│                     │
│ → Net broken        │
│   Floor damaged     │
│   Lights not working│
│   Needs cleaning    │
│                     │
│ Swipe up/down       │
│ Push to confirm     │
└─────────────────────┘
```

**After reporting:**
```
┌─────────────────────┐
│ ISSUE REPORTED! ✓   │
│ ═══════════════════ │
│                     │
│ Scan for details:   │
│   [QR CODE]         │
│                     │
│ Add photo/comments  │
│ via your phone      │
└─────────────────────┘
```

## IR Gesture Click - Recognized Gestures

| Gesture | Action |
|---------|--------|
| **Wave** | Wake up / Start interaction |
| **Swipe Left/Right** | Navigate options |
| **Swipe Up/Down** | Scroll through lists |
| **Push** (toward sensor) | Confirm selection |
| **Hold** | Cancel / Go back |

## LED Matrix Patterns

- **Idle:** Slow pulsing dots (attracting attention)
- **Selecting:** Highlight current option
- **Confirmed:** Big checkmark animation
- **Error:** X pattern with flashing
- **Processing:** Spinning circle animation

## Buzz 2 Click Audio Feedback

- **Short beep:** Selection changed
- **Double beep:** Confirmed
- **Long beep:** Error/invalid gesture
- **Happy chime:** Thank you after submission

## Data Output

**Rating Submission:**
```json
{
  "module_id": "feedback_kiosk_3",
  "court_id": "basketball_a",
  "timestamp": "2025-11-17T15:32:45",
  "rating": 4,
  "rating_type": "overall",
  "maintenance_issue": null,
  "interaction_time_seconds": 8,
  "gesture_used": true,
  "weekly_avg_rating": 4.2,
  "total_ratings_today": 23
}
```

**Maintenance Report:**
```json
{
  "module_id": "feedback_kiosk_3",
  "court_id": "basketball_a",
  "timestamp": "2025-11-17T15:35:12",
  "report_type": "maintenance",
  "issue": "net_broken",
  "qr_code_generated": "https://report.courts.sg/issue/A3F7",
  "priority": "medium",
  "reporter_type": "anonymous"
}
```

## Why This Combination?
- **OLED** = Clear prompts and instructions
- **IR Gesture** = Touchless (hygienic!), futuristic UX
- **LED Matrix** = Engaging visual feedback, attracts attention
- **Buzz** = Audio confirmation (multi-sensory experience)
- **QR Code** = Offload complex input (photos, detailed comments) to phones

## Standalone Value
- Facilities management gets real-time quality scores
- Maintenance issues flagged immediately
- Community sentiment tracking over time
- Validates AI detection: "Users say full but AI says empty? Check camera"
- Gamification potential: "This court has 4.5⭐ rating!"

---

# MODULE 4: SECURITY & MAINTENANCE ALERT DASHBOARD
**"Real-time monitoring for residents, security, and maintenance staff"**

## Hardware Configuration
- **BeagleBone Black Wireless**
- **Click Boards (4/4):**
  1. **OLED Click** - Main alert display
  2. **LED Matrix Click** - Visual status indicators (at-a-glance health)
  3. **Buzz 2 Click** - Audio alerts for urgent issues
  4. **7 Seg 8x8 Click** - Show current active alerts count

## Primary Function
Local monitoring dashboard for facility staff (security guards, maintenance workers, residents) to:
- Monitor unusual activity (e.g., people at 2 AM)
- Receive maintenance alerts (bad ratings, broken equipment)
- Track noise complaints
- View real-time facility status
- Respond quickly to issues

## Deployment Location
Mounted in:
- Security guard post
- Maintenance office
- Resident committee office
- Estate management office

## OLED Display Views

### Default View: System Status
```
┌─────────────────────┐
│ FACILITY MONITOR    │
│ ═══════════════════ │
│ Time: 14:35         │
│                     │
│ ACTIVE ALERTS: 2    │
│                     │
│ Court A: ⚠️ Noise   │
│ Court B: ✓ Normal   │
│ Court C: ⚠️ Rating  │
│                     │
│ Press for details → │
└─────────────────────┘
```

### Alert Detail View (Auto-cycles through active alerts)

**Alert 1: Unusual Activity**
```
┌─────────────────────┐
│ ⚠️ UNUSUAL ACTIVITY │
│ ═══════════════════ │
│ Court A             │
│ Time: 02:15 AM      │
│                     │
│ 5 people detected   │
│ Noise: 68dB         │
│                     │
│ ACTION NEEDED:      │
│ Security check      │
│ recommended         │
│                     │
│ [Buzz: Beep!]       │
└─────────────────────┘
```

**Alert 2: Bad Rating**
```
┌─────────────────────┐
│ ⭐ LOW RATING       │
│ ═══════════════════ │
│ Court C             │
│ Time: 14:22         │
│                     │
│ Rating: ⭐☆☆☆☆      │
│ (1 star - Poor)     │
│                     │
│ ACTION NEEDED:      │
│ Inspection required │
│ Check for issues    │
└─────────────────────┘
```

**Alert 3: Maintenance Issue**
```
┌─────────────────────┐
│ 🔧 MAINTENANCE      │
│ ═══════════════════ │
│ Court A             │
│ Time: 13:45         │
│                     │
│ Reported: Net broken│
│ Reports: 3 today    │
│                     │
│ ACTION NEEDED:      │
│ Repair basketball   │
│ hoop/net            │
└─────────────────────┘
```

**Alert 4: High Noise (Late Night)**
```
┌─────────────────────┐
│ 🔊 NOISE COMPLAINT  │
│ ═══════════════════ │
│ Court B             │
│ Time: 23:45         │
│                     │
│ Noise: 82dB         │
│ (Above threshold)   │
│ 8 people present    │
│                     │
│ ACTION: Check if    │
│ disturbing residents│
└─────────────────────┘
```

**Alert 5: Environmental Hazard**
```
┌─────────────────────┐
│ ☀️ HEAT ADVISORY    │
│ ═══════════════════ │
│ All Courts          │
│ Time: 14:30         │
│                     │
│ Temperature: 38°C   │
│ Heat Index: Extreme │
│                     │
│ RECOMMEND:          │
│ Post warning signs  │
│ Check water coolers │
└─────────────────────┘
```

**Normal Status (No Alerts)**
```
┌─────────────────────┐
│ ✓ ALL CLEAR         │
│ ═══════════════════ │
│                     │
│ Court A: Normal     │
│ Court B: Normal     │
│ Court C: Normal     │
│                     │
│ No active alerts    │
│                     │
│ Last check: 14:35   │
│ Next: 14:36         │
└─────────────────────┘
```

## LED Matrix Click - At-a-Glance Status

Visual patterns show system health without reading display:

**All Green Pattern:** Everything normal
```
█░█░█
░░░░░
█░█░█
░░░░░
█░█░█
```

**Yellow Blinking:** Minor alerts (low ratings, minor issues)
```
░███░
█░░░█
█░░░█
█░░░█
░███░
```

**Red Flashing:** Urgent alerts (unusual activity, noise complaints)
```
█░░░█
░█░█░
░░█░░
░█░█░
█░░░█
```

**Scrolling Pattern:** Multiple alerts, cycling through
```
█████ → ░░░░░ → █████
(Scroll effect showing activity)
```

## 7-Segment Display - Alert Counter

Shows number of active alerts:
```
Display: " 0" = All clear
Display: " 2" = 2 active alerts
Display: " 5" = 5 alerts (busy!)
Display: "Er" = System error
```

Flashes when new alert arrives.

## Buzz 2 Click - Audio Alert System

Different sounds for different urgency levels:

| Alert Type | Sound Pattern | When |
|------------|--------------|------|
| **Unusual Activity (night)** | 3 long beeps | People detected 10PM-6AM |
| **Bad Rating (<2 stars)** | 2 short beeps | Poor quality reported |
| **Maintenance Issue** | Single beep | Equipment broken |
| **Noise Complaint** | Rapid beeps | >80dB after 10PM |
| **Environmental Hazard** | Continuous beep | Extreme heat/danger |
| **New Alert** | Short beep | Any new issue |
| **Alert Cleared** | Pleasant chime | Issue resolved |

**Volume:** Adjustable, defaults to moderate level for office environment.

## Alert Rules & Triggers

### 1. Unusual Activity Detection
```python
if (current_time.hour >= 22 or current_time.hour <= 6) and people_count > 0:
    trigger_alert("unusual_activity", {
        "court_id": court_id,
        "people_count": people_count,
        "noise_db": noise_level,
        "time": current_time,
        "severity": "high",
        "action": "Security check recommended"
    })
```

**Rationale:** Courts should be closed 10PM-6AM. Any activity = potential misuse, vandalism, or noise disturbance.

### 2. Low Rating Alert
```python
if rating <= 2:  # 1 or 2 stars
    trigger_alert("low_rating", {
        "court_id": court_id,
        "rating": rating,
        "time": timestamp,
        "severity": "medium",
        "action": "Inspection required"
    })
```

**Rationale:** Very poor ratings indicate serious quality issues needing immediate attention.

### 3. Maintenance Issue
```python
if maintenance_issue_reported:
    # Count similar reports today
    similar_reports = count_reports(issue_type, today)
    
    trigger_alert("maintenance", {
        "court_id": court_id,
        "issue": issue_type,
        "report_count": similar_reports,
        "severity": "high" if similar_reports >= 3 else "medium",
        "action": f"Repair {issue_type}"
    })
```

**Rationale:** Broken equipment makes courts unusable. Multiple reports = urgent repair needed.

### 4. Noise Complaint (Late Hours)
```python
if (current_time.hour >= 22 or current_time.hour <= 7) and noise_db > 75:
    trigger_alert("noise_complaint", {
        "court_id": court_id,
        "noise_db": noise_level,
        "people_count": people_count,
        "time": current_time,
        "severity": "high",
        "action": "Check if disturbing residents"
    })
```

**Rationale:** Excessive noise late at night disturbs nearby residents. Security should investigate.

### 5. Environmental Hazard
```python
if temperature > 37 or uv_index >= 10:
    trigger_alert("environmental_hazard", {
        "type": "extreme_heat" if temperature > 37 else "extreme_uv",
        "temperature": temperature,
        "uv_index": uv_index,
        "severity": "medium",
        "action": "Post warning signs, check water coolers"
    })
```

**Rationale:** Extreme conditions pose health risks. Staff should post warnings and ensure water availability.

### 6. Equipment Pattern Issues
```python
if rating_trend_7days < 3.0 and rating_count > 10:
    trigger_alert("quality_decline", {
        "court_id": court_id,
        "avg_rating": rating_trend_7days,
        "sample_size": rating_count,
        "severity": "medium",
        "action": "General inspection and maintenance"
    })
```

**Rationale:** Declining ratings over time indicate gradual deterioration needing attention.

## Data Received from Cloud (Every 30 seconds)

```json
{
  "timestamp": "2025-11-17T02:15:00Z",
  "alerts": [
    {
      "id": "alert_001",
      "type": "unusual_activity",
      "court_id": "basketball_a",
      "severity": "high",
      "triggered_at": "2025-11-17T02:15:00Z",
      "data": {
        "people_count": 5,
        "noise_db": 68,
        "time_of_day": "02:15 AM"
      },
      "action_required": "Security check recommended",
      "status": "active"
    },
    {
      "id": "alert_002",
      "type": "low_rating",
      "court_id": "basketball_c",
      "severity": "medium",
      "triggered_at": "2025-11-17T14:22:00Z",
      "data": {
        "rating": 1,
        "rating_stars": "⭐☆☆☆☆"
      },
      "action_required": "Inspection required",
      "status": "active"
    }
  ],
  "system_status": {
    "module1_status": "ok",
    "module2_status": "ok",
    "module3_status": "ok",
    "module5_units": 2,
    "cloud_connection": "ok"
  },
  "court_summary": {
    "basketball_a": {
      "current_people": 5,
      "noise_db": 68,
      "rating_24h_avg": 3.8,
      "status": "alert"
    },
    "basketball_b": {
      "current_people": 0,
      "noise_db": 35,
      "rating_24h_avg": 4.1,
      "status": "normal"
    },
    "basketball_c": {
      "current_people": 2,
      "noise_db": 52,
      "rating_24h_avg": 2.5,
      "status": "alert"
    }
  }
}
```

## Display Update Logic

```python
def update_dashboard():
    """Main dashboard update - runs every 30 seconds"""
    
    # Fetch data from cloud
    data = fetch_from_cloud()
    
    # Update alert counter
    active_alerts = [a for a in data["alerts"] if a["status"] == "active"]
    seven_seg.display(len(active_alerts))
    
    # Update LED Matrix based on severity
    if len(active_alerts) == 0:
        led_matrix.show_pattern("all_clear")
    else:
        highest_severity = max([a["severity"] for a in active_alerts])
        if highest_severity == "high":
            led_matrix.flash_red()
        else:
            led_matrix.blink_yellow()
    
    # Update OLED display
    if len(active_alerts) == 0:
        oled.show_all_clear(data["court_summary"])
    else:
        # Cycle through alerts every 10 seconds
        current_alert = active_alerts[alert_index % len(active_alerts)]
        oled.show_alert_detail(current_alert)
        alert_index += 1
    
    # Check for new alerts and buzz
    new_alerts = [a for a in active_alerts if a["triggered_at"] > last_check_time]
    for alert in new_alerts:
        trigger_buzz(alert["type"], alert["severity"])
    
    last_check_time = now()

def trigger_buzz(alert_type, severity):
    """Sound appropriate alert based on type"""
    
    if alert_type == "unusual_activity":
        buzz.long_beep(count=3)
    elif alert_type == "low_rating":
        buzz.short_beep(count=2)
    elif alert_type == "maintenance":
        buzz.short_beep(count=1)
    elif alert_type == "noise_complaint":
        buzz.rapid_beeps()
    elif alert_type == "environmental_hazard":
        buzz.continuous_beep(duration=2)
```

## Use Case Scenarios

### Scenario 1: Security Guard - Late Night Activity

**Time:** 2:15 AM

**What Happens:**
1. Module 1 detects 5 people at Court A
2. Cloud processes: "Unusual - courts closed"
3. Module 4 receives alert
4. **7-Segment shows:** "1" (1 new alert)
5. **LED Matrix:** Flashes RED
6. **Buzz:** 3 long beeps (urgent)
7. **OLED displays:** Alert details with action needed

**Security Guard Response:**
- Hears buzz, looks at dashboard
- Sees: "5 people at Court A, 2:15 AM"
- Goes to investigate
- Can mark alert as "resolved" via cloud dashboard

### Scenario 2: Maintenance Worker - Poor Rating

**Time:** 2:22 PM

**What Happens:**
1. User gives 1-star rating via Module 3
2. Cloud flags: "Very poor quality"
3. Module 4 receives alert
4. **7-Segment shows:** "1"
5. **LED Matrix:** Blinks YELLOW
6. **Buzz:** 2 short beeps
7. **OLED displays:** Rating + action needed

**Maintenance Worker Response:**
- Checks dashboard during afternoon rounds
- Sees: "Court C rated 1 star"
- Schedules inspection
- Goes to check court condition
- Reports back findings

### Scenario 3: Estate Manager - Multiple Issues

**Time:** Throughout day

**What Happens:**
1. Court A: Noise complaint (10:30 PM)
2. Court B: Net broken report (2:15 PM)
3. Court C: Bad rating (4:22 PM)
4. **7-Segment shows:** "3"
5. **LED Matrix:** Scrolls through alerts
6. **OLED:** Cycles through all 3 alerts

**Estate Manager Response:**
- Reviews dashboard before end of day
- Sees all accumulated issues
- Prioritizes: Noise (urgent), Net (medium), Rating (check tomorrow)
- Assigns tasks to team
- Tracks resolution via cloud

### Scenario 4: Resident Committee - Heat Wave

**Time:** 2:30 PM (Hot day)

**What Happens:**
1. Module 2 detects 38°C temperature
2. Cloud flags: "Environmental hazard"
3. Module 4 receives alert
4. **7-Segment shows:** "1"
5. **LED Matrix:** Blinks YELLOW
6. **Buzz:** Continuous beep (2 seconds)
7. **OLED displays:** Heat advisory

**Resident Committee Response:**
- Checks dashboard after buzz
- Sees: "Extreme heat 38°C"
- Posts warning signs at courts
- Checks water coolers are filled
- Considers temporarily closing courts

## Why This Combination?

- **OLED** = Detailed alert information for decision-making
- **LED Matrix** = At-a-glance status (visible across room)
- **7-Segment** = Quick alert count (how busy is today?)
- **Buzz** = Immediate audio notification (can't miss urgent issues)
- **WiFi** = Receives processed alerts from cloud

## Standalone Value

Even without cloud analytics:
- Can receive direct sensor data from Modules 1-3
- Acts as local monitoring station
- Displays raw sensor readings
- Simple threshold-based alerts
- Manual review of facility status

## Integration Benefits

With cloud processing:
- **Smart filtering:** Only shows actionable alerts
- **Pattern detection:** "This court always has issues on Fridays"
- **Priority ranking:** Most urgent issues first
- **Historical context:** "3rd noise complaint this week"
- **Predictive:** "Court B maintenance due soon based on rating trend"

---

# MODULE 5: SMART COURT INFORMATION DISPLAY
**"Per-court intelligence interface"**

## Hardware Configuration
- **BeagleBone Black Wireless**
- **Click Boards (4/4):**
  1. **OLED Click** - Main information display
  2. **Bar Graph 2 Click** - Hourly pattern visualization
  3. **Analog Key Click** - 5 buttons (navigate views)
  4. **Buzz 2 Click** - Audio feedback for button presses

## Primary Function
Court-specific information terminal that brings all backend intelligence to users right at the court entrance.

## Physical Button Layout (Analog Key Click)

```
┌─────────────────────────────┐
│   [1]  [2]  [3]  [4]  [5]   │
│   Now  His  Wea  Alt  Info  │
└─────────────────────────────┘

Button 1: Current Status
Button 2: History/Patterns  
Button 3: Weather Conditions
Button 4: Alternative Courts
Button 5: Court Information
```

## OLED Display Views

### View 1: Current Status (Default - Button 1)
```
┌─────────────────────┐
│ 🏀 COURT A          │
│ ═══════════════════ │
│                     │
│ NOW: 🔴 FULL        │
│ People: 8           │
│ Est wait: 25 min    │
│                     │
│ Weather: ☀️ 30°C   │
│ Rating: ⭐⭐⭐⭐     │
│                     │
│ Press [2] for best  │
│ times to visit →    │
└─────────────────────┘
```

### View 2A: Today's Pattern (Button 2 - First Press)
```
┌─────────────────────┐
│ TODAY'S PATTERN     │
│ ═══════════════════ │
│                     │
│ 8AM  ░░░░░ Empty   │
│ 10AM ██░░░ Light   │
│ 12PM ████░ Busy    │
│ 2PM  █████ Full    │
│ 3PM  █████ FULL ←  │
│ 5PM  ████░ Busy    │
│ 7PM  ███░░ Moderate│
│ 9PM  ░░░░░ Empty   │
│                     │
│ 💡 Quiet after 8PM  │
│ Press [2] again →   │
└─────────────────────┘
```

### View 2B: Weekly Comparison (Button 2 - Second Press)
```
┌─────────────────────┐
│ THIS TIME WEEKLY    │
│ ═══════════════════ │
│ 3PM Comparison:     │
│                     │
│ MON  ████░ 75%     │
│ TUE  ███░░ 65%     │
│ WED  █████ 90%     │
│ THU  █████ 85% ←   │
│ FRI  █████ 95%     │
│ SAT  ████░ 70%     │
│ SUN  ██░░░ 45%     │
│                     │
│ 💡 Sundays quieter! │
│ Press [1] for now → │
└─────────────────────┘
```

### View 3: Weather Details (Button 3)
```
┌─────────────────────┐
│ WEATHER CONDITIONS  │
│ ═══════════════════ │
│ Temp: 30°C ☀️       │
│ Humidity: 65%       │
│ UV: 9 (Very High)⚠️ │
│ Air Quality: Good ✓ │
│                     │
│ Comfort: 3/5        │
│ [Bar shows: ███░░]  │
│                     │
│ TIPS:               │
│ • Use sunscreen     │
│ • Stay hydrated     │
│ • Best: After 6PM   │
└─────────────────────┘
```

### View 4: Alternative Courts (Button 4)
```
┌─────────────────────┐
│ OTHER COURTS NEARBY │
│ ═══════════════════ │
│                     │
│ THIS: 🔴 FULL (8)   │
│                     │
│ Court B (200m away) │
│ → 🟡 Light (3 ppl)  │
│                     │
│ Court C (500m away) │
│ → 🟢 Empty (0 ppl)  │
│                     │
│ 💡 Court C best now!│
│                     │
│ [Buzz confirms]     │
└─────────────────────┘
```

### View 5: Court Information (Button 5)
```
┌─────────────────────┐
│ COURT INFORMATION   │
│ ═══════════════════ │
│                     │
│ Surface: Rubber     │
│ Lights: 6PM-10PM    │
│ Size: Full court    │
│                     │
│ FACILITIES:         │
│ ✓ Water cooler      │
│ ✓ Covered seating   │
│ ✓ Restrooms nearby  │
│                     │
│ Rating: ⭐⭐⭐⭐ (4.2)│
│ Cleaned: Today 8AM  │
└─────────────────────┘
```

## Bar Graph 2 Click - Always-On Context Display

Regardless of which OLED view is active, the Bar Graph always shows **current 8-hour window around now:**

```
12PM │██░░░ (40% - past data)
1PM  │███░░ (60% - past data)
2PM  │████░ (80% - past data)
3PM  │█████ ← YOU ARE HERE (100% - current)
4PM  │████░ (80% - predicted)
5PM  │█████ (100% - predicted)
6PM  │████░ (80% - predicted)
7PM  │███░░ (60% - predicted)
```

**Left side of "now"** = Historical actual data  
**Right side of "now"** = Predictions from Module 4

This provides instant visual context at all times.

## Buzz 2 Click Audio Feedback

| Event | Sound |
|-------|-------|
| Button press | Short beep |
| View changed | Double beep |
| Alert (court opening) | Triple beep pattern |
| Error/no data | Low buzz |
| Startup | Musical chime |

## Auto-Rotation Mode

If no button pressed for 60 seconds, display automatically cycles through key information:

1. **Current status** (15 seconds)
2. **Today's pattern** (15 seconds)
3. **Best times tip** (15 seconds)
4. **Weather advisory** (15 seconds)
5. **Loop back to current status**

This ensures passers-by always see updated information even without interaction.

## Data Received from Module 4 (Every 30 seconds)

```json
{
  "court_id": "basketball_a",
  "display_unit": "module5_court_a",
  "timestamp": "2025-11-17T15:30:00",
  
  "current": {
    "occupancy": 0.85,
    "people_count": 8,
    "crowd_level": "full",
    "estimated_wait_min": 25,
    "confidence": 0.92,
    "last_update": "30 seconds ago"
  },
  
  "weather": {
    "temp_c": 30,
    "humidity_percent": 65,
    "uv_index": 9,
    "voc_level": "good",
    "comfort_score": 3.2,
    "warnings": ["high_uv"],
    "recommendations": ["sunscreen", "hydration"]
  },
  
  "patterns": {
    "today_hourly": [
      {"hour": 8, "occupancy": 0.20},
      {"hour": 10, "occupancy": 0.40},
      {"hour": 12, "occupancy": 0.80},
      {"hour": 14, "occupancy": 1.0},
      {"hour": 15, "occupancy": 1.0},
      {"hour": 17, "occupancy": 0.80},
      {"hour": 19, "occupancy": 0.60},
      {"hour": 21, "occupancy": 0.10}
    ],
    "week_same_time": [
      {"day": "Mon", "occupancy": 0.75},
      {"day": "Tue", "occupancy": 0.65},
      {"day": "Wed", "occupancy": 0.90},
      {"day": "Thu", "occupancy": 0.85},
      {"day": "Fri", "occupancy": 0.95},
      {"day": "Sat", "occupancy": 0.70},
      {"day": "Sun", "occupancy": 0.45}
    ]
  },
  
  "recommendations": {
    "best_times_today": ["07:00-09:00", "14:00-16:00", "20:00-22:00"],
    "avoid_times": ["17:00-19:00"],
    "next_available_slot": "16:15",
    "nearby_alternatives": [
      {
        "id": "basketball_b",
        "name": "Court B",
        "distance_m": 200,
        "occupancy": 0.30,
        "people": 3,
        "status": "light"
      },
      {
        "id": "basketball_c", 
        "name": "Court C",
        "distance_m": 500,
        "occupancy": 0.0,
        "people": 0,
        "status": "empty"
      }
    ]
  },
  
  "info": {
    "court_name": "Basketball Court A",
    "type": "outdoor",
    "surface": "rubber",
    "lighting_hours": "18:00-22:00",
    "rating_avg": 4.2,
    "rating_count": 47,
    "last_cleaned": "2025-11-17T08:00:00",
    "facilities": ["water_cooler", "covered_seating", "restrooms"]
  }
}
```

## Display Update Logic

```python
def update_display():
    """Main display update loop - runs every 30 seconds"""
    
    # Fetch latest data from Module 4
    data = fetch_from_module4(court_id)
    
    # Update Bar Graph (always visible)
    update_bar_graph(data["patterns"]["today_hourly"])
    
    # Update OLED based on current view
    if current_view == "status":
        show_current_status(data["current"], data["weather"], data["info"])
    elif current_view == "history_today":
        show_today_pattern(data["patterns"]["today_hourly"])
    elif current_view == "history_week":
        show_weekly_comparison(data["patterns"]["week_same_time"])
    elif current_view == "weather":
        show_weather_details(data["weather"])
    elif current_view == "alternatives":
        show_nearby_courts(data["recommendations"]["nearby_alternatives"])
    elif current_view == "info":
        show_court_info(data["info"])
    
    # Check for alerts
    if data["current"]["crowd_level"] == "empty" and previous_level == "full":
        trigger_alert()  # Buzz + LED notification

def handle_button_press(button_id):
    """Handle user button interactions"""
    
    # Buzz feedback
    buzz_click.short_beep()
    
    # Change view
    if button_id == 1:
        current_view = "status"
    elif button_id == 2:
        if current_view == "history_today":
            current_view = "history_week"  # Toggle between today/week
        else:
            current_view = "history_today"
    elif button_id == 3:
        current_view = "weather"
    elif button_id == 4:
        current_view = "alternatives"
    elif button_id == 5:
        current_view = "info"
    
    # Reset auto-rotation timer
    last_interaction_time = now()
    
    # Update display immediately
    update_display()

def auto_rotation():
    """Auto-cycle through views if no user interaction"""
    
    if (now() - last_interaction_time) > 60:  # 60 seconds idle
        rotation_views = ["status", "history_today", "weather", "status"]
        current_view = rotation_views[rotation_index % len(rotation_views)]
        rotation_index += 1
```

## Why This Combination?
- **OLED** = Clear, detailed text information
- **Bar Graph** = Always-visible hourly context (no button press needed)
- **Analog Key (5 buttons)** = Simple navigation, all views easily accessible
- **Buzz** = Satisfying audio feedback for interactions
- **WiFi** = Receives real-time updates from Module 4 every 30 seconds

## Standalone Value
Even without other modules, Module 5 can:
- Display static court information (hours, rules, facilities)
- Show weather data (if Module 2 connected directly)
- Act as information kiosk with manually updated content
- Serve as wayfinding display for sports complex

## Progressive Enhancement
- **With Module 4 only:** Shows predictions but no real-time validation
- **With Module 1 added:** Gains live crowd counts
- **With Module 2 added:** Weather context explains patterns
- **With Module 3 added:** User ratings add quality dimension
- **Full system:** Complete intelligent information hub

---

# 🔗 SYSTEM INTEGRATION

## Communication Architecture

```
                    ┌─────────────────┐
                    │  CLOUD SERVER   │
                    │   (Analytics)   │
                    │  - Stores data  │
                    │  - Predictions  │
                    │  - Alerts       │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐         ┌────▼────┐        ┌────▼────┐
    │ MODULE 1│         │ MODULE 2│        │ MODULE 3│
    │ (Crowd) │         │  (Env)  │        │(Feedback)│
    │ Sends:  │         │ Sends:  │        │ Sends:  │
    │ • Count │         │ • Temp  │        │ • Rating│
    │ • Noise │         │ • UV    │        │ • Issues│
    └─────────┘         └─────────┘        └─────────┘
                             │
                    ┌────────▼────────┐
                    │  CLOUD SERVER   │
                    │   (Processes)   │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐         ┌────▼────┐        ┌────▼────┐
    │ MODULE 4│         │ MODULE 5│        │ MODULE 5│
    │Security │         │ Court A │        │ Court B │
    │Dashboard│         │ Display │        │ Display │
    └─────────┘         └─────────┘        └─────────┘
```

## WiFi Communication Protocol

### MQTT Topics Structure:**
```
sports-facility/
├── sensor-data/
│   ├── basketball-a/
│   │   ├── crowd          (Module 1 → Cloud)
│   │   ├── environment    (Module 2 → Cloud)
│   │   └── feedback       (Module 3 → Cloud)
│   ├── basketball-b/
│   │   └── ...
│   └── basketball-c/
│       └── ...
├── displays/
│   ├── security-dashboard (Cloud → Module 4)
│   ├── court-a-display    (Cloud → Module 5)
│   └── court-b-display    (Cloud → Module 5)
└── system/
    ├── health             (All modules → Cloud)
    ├── commands           (Cloud → All modules)
    └── alerts             (Cloud → Module 4)
```

### Message Format (JSON over MQTT)

**Module 1 → Cloud:**
```json
{
  "topic": "sports-facility/sensor-data/basketball-a/crowd",
  "timestamp": "2025-11-17T15:30:00Z",
  "module_id": "crowd_unit_1",
  "data": {
    "people_count": 8,
    "crowd_level": "full",
    "noise_db": 75,
    "motion_detected": true,
    "proximity_triggered": true,
    "confidence": 0.95
  }
}
```

**Module 2 → Cloud:**
```json
{
  "topic": "sports-facility/sensor-data/basketball-a/environment",
  "timestamp": "2025-11-17T15:30:00Z",
  "module_id": "environment_unit_2",
  "data": {
    "temperature_c": 32,
    "humidity_percent": 78,
    "uv_index": 9,
    "voc_level": "good",
    "comfort_score": 3.0
  }
}
```

**Module 3 → Cloud:**
```json
{
  "topic": "sports-facility/sensor-data/basketball-a/feedback",
  "timestamp": "2025-11-17T15:32:45Z",
  "module_id": "feedback_kiosk_3",
  "data": {
    "rating": 4,
    "maintenance_issue": null,
    "interaction_time_seconds": 8
  }
}
```

**Cloud → Module 4 (Security Dashboard):**
```json
{
  "topic": "sports-facility/displays/security-dashboard",
  "timestamp": "2025-11-17T15:30:00Z",
  "alerts": [
    {
      "id": "alert_001",
      "type": "unusual_activity",
      "court_id": "basketball_a",
      "severity": "high",
      "data": {...},
      "action_required": "Security check recommended"
    }
  ],
  "court_summary": {...}
}
```

**Cloud → Module 5 (Court Display):**
```json
{
  "topic": "sports-facility/displays/court-a-display",
  "timestamp": "2025-11-17T15:30:00Z",
  "court_id": "basketball_a",
  "current": {
    "occupancy": 0.85,
    "people_count": 8,
    "crowd_level": "full",
    "estimated_wait_min": 25
  },
  "weather": {...},
  "patterns": {...},
  "recommendations": {...}
}
```

## Data Flow Timeline

### Every 30 Seconds:

**T+0s:** Module 1 captures webcam image, reads sensors  
**T+2s:** Module 1 sends data to Google AI for processing  
**T+5s:** Module 1 publishes results to Cloud  
**T+6s:** Module 2 reads environment sensors  
**T+7s:** Module 2 publishes to Cloud  
**T+8s:** Cloud receives all sensor data  
**T+10s:** Cloud processes data, runs predictions, detects alerts  
**T+12s:** Cloud broadcasts to Module 4 (security) and all Module 5 units  
**T+13s:** All displays update  

**When user interacts with Module 3:**
- Immediate: Gesture detected, display updates
- Within 1s: Data sent to Cloud
- Within 2s: Cloud updates average rating, checks for alert thresholds
- Within 35s: New rating appears on all displays (next cycle)
- If rating ≤ 2 stars: Module 4 gets immediate alert

**Cloud Processing:**
- **Stores** all sensor data in time-series database
- **Analyzes** 30+ days of historical patterns
- **Predicts** next hour occupancy for each court
- **Generates** best time recommendations
- **Detects** anomalies and alert conditions
- **Broadcasts** processed insights to displays

## Scalability

### Adding More Courts:

**Minimal deployment (1 court):**
- 1x Module 1 (crowd detection)
- 1x Module 2 (environment - can be shared)
- 1x Module 3 (feedback - can be shared)
- 1x Module 4 (central hub)
- 1x Module 5 (display at court)

**Medium facility (3 courts):**
- 3x Module 1 (one per court)
- 1x Module 2 (shared, centrally located)
- 1x Module 3 (shared, central kiosk)
- 1x Module 4 (central hub)
- 3x Module 5 (one per court entrance)

**Large facility (10+ courts):**
- 10x Module 1 (one per court)
- 2-3x Module 2 (different zones for microclimate)
- 2x Module 3 (distributed for convenience)
- 1x Module 4 (can handle 50+ courts)
- 10x Module 5 (one per court)

### Module 4 Can Support:
- Up to 50 courts simultaneously
- 30+ days of historical data per court
- Predictions for all courts every 30 seconds
- 100+ Module 5 display units
- 10+ Module 1 sensor units
- 5+ Module 2 environment stations
- 5+ Module 3 feedback kiosks

---

# 💡 USE CASE SCENARIOS

## Scenario 1: Young Adult Wants to Play Basketball

**Without System:**
- Travels 20 minutes to court
- Finds it full
- Waits 30 minutes or gives up
- Wasted 50+ minutes

**With System:**
1. Sees Module 5 display before leaving home (via web dashboard)
2. Learns: "Court A is FULL. Court C is empty (500m away)"
3. Goes directly to Court C
4. Plays immediately
5. **Saved 50 minutes + frustration**

## Scenario 2: User Arrives at Full Court

**Without System:**
- Uncertain how long to wait
- No idea if anyone is leaving soon
- May give up or waste time waiting

**With System:**
1. Checks Module 5 display at court entrance
2. Sees: "Estimated wait: 25 minutes"
3. Views alternative: "Court B nearby - Light (3 people)"
4. Checks weather: "30°C now, cooler at 6PM"
5. **Makes informed decision:** Go to Court B or come back at 6PM

## Scenario 3: Planning Weekly Sports Session

**Without System:**
- Trial and error to find good times
- Random scheduling leads to crowded courts

**With System:**
1. Checks Module 5 historical patterns
2. Sees: "Sundays 9AM typically 45% occupied"
3. Avoids: "Fridays 6PM typically 95% occupied"
4. **Optimizes schedule** for best experience

## Scenario 4: Facilities Management

**Without System:**
- No data on court usage
- Random maintenance schedules
- Can't justify budget for improvements

**With System:**
1. Module 4 dashboard shows utilization rates
2. Discovers: "Court A used 85%, Court C only 30%"
3. Schedules maintenance during low-usage times
4. Uses rating data to prioritize repairs
5. **Data-driven decisions + better resource allocation**

## Scenario 5: Safety Concerns

**Without System:**
- Users play in dangerous heat
- No UV awareness
- Poor air quality goes unnoticed

**With System:**
1. Module 2 detects dangerous conditions
2. Module 5 displays warnings: "Heat Index: 40°C - Caution!"
3. Recommendations: "Play after 6PM" + "Use sunscreen"
4. **Prevents heat stroke and sun damage**

---

# 📊 SYSTEM VALUE PROPOSITION

## For Users (19-30 year olds living with parents)

### Problems Solved:
✅ **Wasted trips** - Know before you go  
✅ **Court hunting** - See all nearby options  
✅ **Uncertainty** - Clear wait time estimates  
✅ **Poor planning** - Learn best times to visit  
✅ **Safety** - Weather warnings and recommendations

### Time Saved:
- Average 30-45 minutes per visit
- Reduced frustration
- Better sports experience

### Survey Validation:
- Q6: "Traveled there only to find no courts" → **SOLVED by Module 5**
- Q7: "Had to wait 30+ minutes" → **SOLVED by predictions**
- Q9: "How often do issues prevent you from playing?" → **REDUCED significantly**
- Q15: "Would you play MORE often if..." → **YES, 30% increase expected**

## For Facilities Management

### Benefits:
✅ **Real-time alerts** - Immediate notification of issues  
✅ **24/7 monitoring** - Security dashboard never sleeps  
✅ **Maintenance optimization** - Fix issues before they escalate  
✅ **Utilization data** - Understand actual usage patterns  
✅ **User satisfaction tracking** - Real-time quality ratings  
✅ **Budget justification** - Data for expansion/improvement requests  
✅ **Staff efficiency** - Prioritized task list based on severity

### Specific Use Cases:

**Security Guard:**
- Module 4 alerts to unusual late-night activity
- Can investigate before complaints arise
- Data for incident reports

**Maintenance Worker:**
- Module 4 shows broken equipment reports
- Priority ranking (3 reports = urgent)
- Can plan repair schedule efficiently

**Estate Manager:**
- Module 4 dashboard shows daily summary
- Tracks trend: "Court B always problematic"
- Allocates budget for targeted improvements

### ROI:
- Faster response to issues (minutes vs. days)
- Reduced complaints from residents
- Better resource allocation
- Increased user satisfaction
- Data-driven planning
- Preventive vs. reactive maintenance

## For Community

### Benefits:
✅ **Fair access** - Information levels playing field  
✅ **Increased participation** - Reduced barriers to sports  
✅ **Health & safety** - Environmental monitoring  
✅ **Community engagement** - Feedback mechanism  
✅ **Transparency** - Open data about public facilities

---

# 🔧 TECHNICAL SPECIFICATIONS

## Hardware Summary

| Module | BeagleBone | Click Boards | Additional | Primary User |
|--------|-----------|--------------|------------|--------------|
| **Module 1** | BBB Wireless | MIC, Motion, OLED, Proximity | USB Webcam | Automated |
| **Module 2** | BBB Wireless | Environment, UV3, Bar Graph, OLED | - | Automated |
| **Module 3** | BBB Wireless | OLED, IR Gesture, LED Matrix, Buzz2 | - | Public users |
| **Module 4** | BBB Wireless | OLED, LED Matrix, 7-Seg, Buzz2 | - | Security/Maintenance |
| **Module 5** | BBB Wireless | OLED, Bar Graph, Analog Key, Buzz2 | - | Public users |

**Cloud Server:**
- Backend server (can be AWS, Azure, Google Cloud, or local server)
- Handles all analytics, predictions, pattern learning
- Stores historical data (database)
- Runs machine learning models
- Generates alerts based on rules
- Web dashboard for remote access

## Power Requirements

**Per Module:**
- BeagleBone Black Wireless: 5V @ 1A (typical)
- Click boards: 3.3V/5V @ 100-500mA total
- Total per module: ~5V @ 2A max

**System Total (5 modules):**
- ~10A @ 5V = 50W
- Recommend 60W power supply for headroom

## Network Requirements

**WiFi:**
- 802.11 b/g/n
- 2.4 GHz band
- MQTT broker accessible on local network
- Bandwidth: <10 KB/s per module (very light)

**MQTT Broker:**
- Mosquitto or similar
- Can run on Module 4 or separate server
- QoS 1 (at least once delivery)

## Software Stack

**Operating System:**
- Debian Linux (BeagleBone standard)

**Programming Language:**
- Python 3.7+

**Key Libraries:**
- `paho-mqtt` - MQTT communication
- `opencv-python` - Webcam processing (Module 1)
- `google-generativeai` - Google AI API (Module 1)
- `numpy` - Data processing
- `json` - Data serialization
- BeagleBone GPIO libraries for Click boards

**External Services:**
- Google AI Pro API (for image recognition in Module 1)
- Cloud server / hosting (for analytics and data storage)
- MQTT broker (can be hosted on cloud or local server)

---

# 🚀 DEPLOYMENT ROADMAP

## Phase 1: Proof of Concept (Weeks 1-4)

**Goal:** Validate core concept with single court

**Deploy:**
- 1x Module 1 (crowd detection)
- 1x Module 5 (public display)
- Cloud server (basic setup)

**Validate:**
- Webcam + AI accuracy
- Cloud connectivity and data flow
- User engagement with display
- Basic predictions work

## Phase 2: Full Single Court (Weeks 5-8)

**Goal:** Complete feature set for one court

**Add:**
- 1x Module 2 (environment)
- 1x Module 3 (feedback)
- 1x Module 4 (security dashboard)
- Cloud analytics enhanced

**Validate:**
- Multi-sensor fusion accuracy
- Gesture interaction usability
- Weather impact on predictions
- User rating system engagement
- Security alert system works

## Phase 3: Multi-Court Expansion (Weeks 9-12)

**Goal:** Scale to 3 courts, validate cross-court features

**Add:**
- 2x Module 1 (Courts B & C)
- 2x Module 5 (Courts B & C)
- Scale cloud infrastructure

**Validate:**
- Alternative court recommendations
- Load balancing across facilities
- Cloud handles multiple data streams
- Cross-court comparisons work
- Security dashboard shows all courts

## Phase 4: Optimization & Polish (Weeks 13-16)

**Goal:** Refine based on user and staff feedback

**Focus:**
- UI/UX improvements
- Prediction accuracy tuning
- Alert threshold optimization
- Performance optimization
- Bug fixes
- Documentation
- Training for security/maintenance staff

---

# 🎓 EDUCATIONAL VALUE

## Learning Outcomes

### Hardware Integration:
- Multi-sensor fusion techniques
- Click board interfacing
- BeagleBone GPIO programming
- Power management for outdoor deployment

### Software Engineering:
- MQTT pub/sub architecture
- Real-time data processing
- API integration (Google AI)
- Database design for time-series data

### Data Science:
- Pattern recognition in usage data
- Prediction algorithm development
- Anomaly detection
- Confidence scoring

### User Experience:
- Gesture-based interfaces
- Multi-modal feedback (visual + audio + haptic)
- Information architecture
- Auto-cycling displays

### Systems Thinking:
- Modular architecture design
- Scalability considerations
- Fault tolerance
- Progressive enhancement

---

# 📋 SUCCESS METRICS

## Technical Metrics

- **Prediction Accuracy:** >85% within ±15 minutes
- **Sensor Uptime:** >99% availability
- **Response Time:** <500ms for display updates
- **Confidence Score:** >90% for crowd detection

## User Metrics

- **Display Engagement:** >30% of visitors check display
- **Time Saved:** Average 30 minutes per visit
- **User Satisfaction:** >4.0/5.0 average rating
- **Repeat Usage:** >60% check before returning

## System Metrics

- **Court Utilization:** Increase 15-20% in off-peak hours
- **Wasted Trips:** Reduce by 70%
- **Maintenance Response:** <24 hours for reported issues
- **Data Collection:** 30+ days continuous operation

---

# 🔐 PRIVACY & SECURITY

## Data Privacy

### What We Collect:
- Anonymous crowd counts (no facial recognition)
- Environmental readings (public data)
- Anonymous ratings (no user identification)
- Usage patterns (aggregated only)

### What We DON'T Collect:
- Individual faces or identities
- Personal information
- Tracking of specific users
- Location data of individuals

## Security Measures

- WiFi network encryption (WPA2)
- MQTT authentication
- No cloud storage of video (processed locally)
- Encrypted data transmission
- Regular security updates

## Compliance

- PDPA (Singapore Personal Data Protection Act) compliant
- No PII (Personally Identifiable Information) collected
- Transparent data usage policy
- User consent for feedback submission

---

# ✅ CONCLUSION

This 5-module system provides a **complete, scalable solution** to the core problem: uncertainty and frustration when using public sports facilities.

## Key Strengths:

1. **Modular Design** - Each module is useful standalone, better together
2. **Multi-Sensor Validation** - High accuracy through data fusion
3. **Dual User Focus** - Serves both public users AND facility staff
4. **Cloud-Powered** - Scalable analytics without hardware limitations
5. **Real-Time Alerts** - Proactive management vs. reactive complaints
6. **User-Centric** - Solves real pain points identified in survey
7. **Scalable** - Starts with 1 court, grows to unlimited
8. **Future-Proof** - Gesture UI, AI processing, cloud-ready

## Innovation Highlights:

- **Touchless gesture interaction** (Module 3)
- **Multi-modal feedback** (visual + audio + haptic)
- **Security alert system** (Module 4 - unique feature)
- **Predictive analytics** with weather correlation (Cloud)
- **Cross-court intelligence** (system-wide optimization)
- **Progressive enhancement** (works partially, improves with full deployment)

## Unique Value of Module 4:

**Unlike typical smart city solutions that only serve end-users, this system also serves the facility operators:**

✅ **Security guards** get alerted to unusual activity  
✅ **Maintenance workers** receive prioritized repair lists  
✅ **Estate managers** see data-driven insights  
✅ **Residents** benefit from proactive management

This creates a **complete ecosystem** where both users and operators benefit.

## Target User Validation:

Perfect for **19-30 year olds living with parents** because:
- ✅ Saves time (valuable for busy schedules)
- ✅ Reduces wasted trips (limited transportation budget)
- ✅ Enables better planning (fits around family commitments)
- ✅ Intuitive tech interface (tech-native generation)
- ✅ Free public facilities (budget-conscious)

---

**Ready for deployment and real-world validation!** 🚀
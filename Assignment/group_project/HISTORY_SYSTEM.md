# Historical Data Storage System

## Overview

The system now tracks historical data for all modules with minute-based averaging and supports both SQLite database (default) and JSON file storage.

## Features

- **Minute-based averaging**: Data is collected for 1 minute, then averaged and saved
- **SQLite database**: Simple, no external setup required (default)
- **JSON fallback**: Can switch to JSON files if needed
- **Timestamp storage**: All data includes ISO format timestamps
- **Multi-module support**: Tracks data from all modules

## Modules Tracked

### Module 1: Crowd Detection
- **Table**: `module1_crowd`
- **Data**: `people_count`, `noise_db` (audio)
- **Averaged**: Yes (every minute)

### Module 1: Audio
- **Table**: `module1_audio`
- **Data**: `noise_db` (decibel levels)
- **Averaged**: Yes (every minute)

### Module 2: Environment
- **Table**: `module2_environment`
- **Data**: `temperature_c`, `humidity_percent`, `pressure_hpa`, `uv_index`, `voc_level`, `comfort_score`
- **Averaged**: Yes (every minute)

### Module 3: Feedback
- **Table**: `module3_feedback`
- **Data**: `rating` (1-5), `report_type`
- **Averaged**: No (saved immediately when rating occurs)

## Configuration

In `server.py`, you can configure:

```python
USE_DATABASE = True  # Set to False to use JSON files instead
```

- **True**: Uses SQLite database (`history.db`) - recommended
- **False**: Uses JSON files (backward compatible with existing `history.json`)

## Database Location

- **SQLite**: `history.db` (in same directory as server.py)
- **JSON**: `history.json` (for Module 1 crowd data only, when USE_DATABASE=False)

## How It Works

1. **Data Collection**: As data arrives from modules, it's added to minute buffers
2. **Averaging**: Every 60 seconds, data in buffers is averaged
3. **Storage**: Averages are saved to database/JSON with timestamp
4. **Feedback**: Module 3 ratings are saved immediately (not averaged)

## Querying Historical Data

Use the `get_history_from_db()` function:

```python
# Get last 1000 Module 2 environment readings
env_data = get_history_from_db('module2_environment', limit=1000)

# Get Module 1 crowd data from last 24 hours
from datetime import datetime, timedelta
start = datetime.now() - timedelta(days=1)
crowd_data = get_history_from_db('module1_crowd', start_date=start)

# Get Module 3 feedback from date range
start = datetime(2026, 1, 1)
end = datetime(2026, 1, 31)
feedback_data = get_history_from_db('module3_feedback', start_date=start, end_date=end)
```

## Database Schema

### module1_crowd
```sql
CREATE TABLE module1_crowd (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    people_count INTEGER,
    noise_db REAL,
    UNIQUE(timestamp)
)
```

### module1_audio
```sql
CREATE TABLE module1_audio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    noise_db REAL,
    UNIQUE(timestamp)
)
```

### module2_environment
```sql
CREATE TABLE module2_environment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    temperature_c REAL,
    humidity_percent REAL,
    pressure_hpa REAL,
    uv_index REAL,
    voc_level TEXT,
    comfort_score REAL,
    UNIQUE(timestamp)
)
```

### module3_feedback
```sql
CREATE TABLE module3_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    rating INTEGER,
    report_type TEXT,
    UNIQUE(timestamp)
)
```

## Advantages of SQLite

- **No external setup**: SQLite is included with Python
- **Efficient queries**: Fast indexed lookups by timestamp
- **Scalable**: Handles large amounts of data efficiently
- **Standard SQL**: Easy to query with standard SQL tools
- **ACID compliant**: Reliable data storage

## Migration

If you have existing `history.json` data, it will continue to work. The system:
- Uses database for new data (Module 1, 2, 3)
- Falls back to JSON for Module 1 crowd data if `USE_DATABASE=False`
- Old JSON data is preserved and can be queried separately

## External Database Options

If you want to use PostgreSQL, MySQL, or another database:

1. Install the appropriate Python driver (e.g., `psycopg2` for PostgreSQL)
2. Modify `init_database()` to use your database connection
3. Update connection strings in `save_minute_averages()` and `get_history_from_db()`

Example for PostgreSQL:
```python
import psycopg2

def init_database():
    conn = psycopg2.connect(
        host="localhost",
        database="history_db",
        user="your_user",
        password="your_password"
    )
    # ... create tables ...
```

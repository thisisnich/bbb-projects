#!/usr/bin/env python3
"""
One-off migration: update existing timestamp columns to use UTC with 'Z' suffix.
Run from Assignment/group_project: python migrate_timestamps_to_utc_z.py
"""
import os
import re
import sqlite3

# Same paths as server.py
BASE = os.path.dirname(os.path.abspath(__file__))
RATING_DB = os.path.join(BASE, 'rating.db')
CROWD_DB = os.path.join(BASE, 'crowd.db')
ENV_DB = os.path.join(BASE, 'env.db')
HISTORY_DB = os.path.join(BASE, 'history.db')

# (db_path, table_name, timestamp_column)
DB_TABLES = [
    (RATING_DB, 'rating_data', 'timestamp'),
    (CROWD_DB, 'crowd_data', 'timestamp'),
    (ENV_DB, 'env_data', 'timestamp'),
    (HISTORY_DB, 'module1_crowd', 'timestamp'),
    (HISTORY_DB, 'module1_audio', 'timestamp'),
    (HISTORY_DB, 'module2_environment', 'timestamp'),
    (HISTORY_DB, 'module3_feedback', 'timestamp'),
]

def needs_z(ts):
    """True if value should get 'Z' appended (no timezone indicator)."""
    if not ts or not isinstance(ts, str):
        return False
    s = ts.strip()
    if s.endswith('Z'):
        return False
    # Ends with +00:00, -05:00, etc.
    if re.search(r'[+-]\d{2}:?\d{2}$', s):
        return False
    return True

def migrate_table(conn, table: str, ts_col: str) -> int:
    cursor = conn.cursor()
    cursor.execute(f'SELECT id, "{ts_col}" FROM "{table}"')
    rows = cursor.fetchall()
    updated = 0
    for row in rows:
        id_, ts = row[0], row[1]
        if not needs_z(ts):
            continue
        new_ts = ts.rstrip() + 'Z'
        cursor.execute(f'UPDATE "{table}" SET "{ts_col}" = ? WHERE id = ?', (new_ts, id_))
        updated += 1
    conn.commit()
    return updated

def main():
    total = 0
    for db_path, table, ts_col in DB_TABLES:
        if not os.path.exists(db_path):
            print(f'Skip (missing): {db_path}')
            continue
        try:
            conn = sqlite3.connect(db_path)
            n = migrate_table(conn, table, ts_col)
            conn.close()
            if n > 0:
                print(f'{os.path.basename(db_path)} / {table}: updated {n} row(s)')
                total += n
        except Exception as e:
            print(f'Error {db_path} / {table}: {e}')
    if total == 0:
        print('No timestamps needed updating (all already use Z or timezone).')
    else:
        print(f'Done. Total rows updated: {total}')

if __name__ == '__main__':
    main()

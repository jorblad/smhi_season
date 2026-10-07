"""Inject historical temperature records into Home Assistant SQLite DB."""

import sqlite3
from datetime import datetime, timedelta, timezone

# Path to the SQLite database in your dev config
DB_PATH = "config/home-assistant_v2.db"
SENSOR_ENTITY_ID = "sensor.mock_outside_temperature"


def inject_daily_temps(temp_list: list[float]):
    """
    Inject temperatures for past days.
    temp_list: list of daily temps starting from oldest to yesterday.
    E.g., [12.0, 11.5, 13.0, 12.5, 14.0] for a 5-day streak.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get metadata_id for the entity
    cursor.execute(
        "SELECT metadata_id FROM states_meta WHERE entity_id = ?", (SENSOR_ENTITY_ID,)
    )
    row = cursor.fetchone()
    if not row:
        print(
            f"Error: Entity {SENSOR_ENTITY_ID} not found in database. "
            "Make sure HA has started at least once."
        )
        return

    metadata_id = row[0]
    now_utc = datetime.now(timezone.utc)

    num_days = len(temp_list)
    for idx, temp in enumerate(temp_list):
        # Calculate target date: (num_days - idx) days ago at 12:00 UTC
        target_date = now_utc - timedelta(days=num_days - idx)
        target_date = target_date.replace(hour=12, minute=0, second=0, microsecond=0)
        ts_utc = target_date.timestamp()

        # Insert state record
        cursor.execute(
            """
            INSERT INTO states
                (metadata_id, state, last_updated_ts, last_reported_ts, last_changed_ts)
            VALUES (?, ?, ?, ?, ?)
            """,
            (metadata_id, str(temp), ts_utc, ts_utc, ts_utc),
        )
        print(
            f"Injected {temp}°C for date: {target_date.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    conn.commit()
    conn.close()
    print("Successfully backfilled history!")


if __name__ == "__main__":
    # Example: Inject 5 consecutive days of summer temperatures (>= 10.0°C)
    summer_streak = [12.0, 11.5, 13.0, 12.5, 14.0]

    # Example: Inject 7 consecutive days of spring temperatures (> 0.0°C and < 10.0°C)
    # spring_streak = [5.0, 6.0, 4.5, 7.0, 5.5, 6.2, 5.8]

    inject_daily_temps(summer_streak)

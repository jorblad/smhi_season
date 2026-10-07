"""Test SMHI Season sensor state machine."""

from datetime import date, timedelta

import pytest
from homeassistant.util import dt as dt_util

from custom_components.smhi_season.const import (
    SEASON_SOMMAR,
    SEASON_VAR,
    SEASON_VINTER,
)
from custom_components.smhi_season.sensor import SMHISeasonSensor


class MockConfigEntry:
    entry_id = "test_entry_id"
    data = {"temperature_sensor": "sensor.outdoor_temperature"}


@pytest.mark.asyncio
async def test_smhi_season_sensor_init():
    """Test initial sensor attributes."""
    entry = MockConfigEntry()
    sensor = SMHISeasonSensor(entry, "sensor.outdoor_temperature")

    assert sensor.native_value == SEASON_VINTER
    assert sensor.extra_state_attributes["streak_count"] == 0
    assert sensor.extra_state_attributes["target_season"] is None


@pytest.mark.asyncio
async def test_spring_transition_streak():
    """Test spring requires 7 consecutive days >= Feb 15."""
    entry = MockConfigEntry()
    sensor = SMHISeasonSensor(entry, "sensor.outdoor_temperature")

    # Temperatures between 0.0 and 10.0 starting Feb 15
    for i in range(1, 7):
        test_date = date(2026, 2, 14 + i)
        await sensor._evaluate_smhi_rules(test_date, 5.0)
        assert sensor.native_value == SEASON_VINTER  # Not changed yet
        assert sensor.extra_state_attributes["streak_count"] == i
        assert sensor.extra_state_attributes["target_season"] == SEASON_VAR

    # 7th day triggers spring
    await sensor._evaluate_smhi_rules(date(2026, 2, 21), 5.0)
    assert sensor.native_value == SEASON_VAR
    assert sensor.extra_state_attributes["season_start_date"] == "2026-02-15"


@pytest.mark.asyncio
async def test_spring_blocked_before_feb_15():
    """Test spring candidate is ignored before Feb 15."""
    entry = MockConfigEntry()
    sensor = SMHISeasonSensor(entry, "sensor.outdoor_temperature")

    # 5.0°C in early February should not count toward Spring streak
    await sensor._evaluate_smhi_rules(date(2026, 2, 10), 5.0)
    assert sensor.native_value == SEASON_VINTER
    assert sensor.extra_state_attributes["streak_count"] == 0
    assert sensor.extra_state_attributes["target_season"] is None


@pytest.mark.asyncio
async def test_summer_transition_streak():
    """Test summer requires 5 consecutive days >= 10.0°C."""
    entry = MockConfigEntry()
    sensor = SMHISeasonSensor(entry, "sensor.outdoor_temperature")
    sensor._state = SEASON_VAR

    for i in range(1, 5):
        test_date = date(2026, 5, i)
        await sensor._evaluate_smhi_rules(test_date, 12.0)
        assert sensor.native_value == SEASON_VAR
        assert sensor.extra_state_attributes["streak_count"] == i

    # 5th day triggers summer
    await sensor._evaluate_smhi_rules(date(2026, 5, 5), 12.0)
    assert sensor.native_value == SEASON_SOMMAR
    assert sensor.extra_state_attributes["season_start_date"] == "2026-05-01"


@pytest.mark.asyncio
async def test_replay_history_backfill():
    """Backfilled summer data must flip the season without waiting days.

    Reproduces the bug where a long -30 period was already processed day by day
    as winter, and later backfilling corrected summer data never took effect
    because the sensor only advances one day at a time.
    """
    entry = MockConfigEntry()
    sensor = SMHISeasonSensor(entry, "sensor.outdoor_temperature")
    sensor._state = SEASON_VINTER  # as if it had been stuck on winter

    # Five consecutive backfilled summer days ending yesterday.
    today = dt_util.now().date()
    means = {(today - timedelta(days=n)).isoformat(): 12.0 for n in range(1, 6)}

    async def fake_get_daily_means(start, end):
        return means

    sensor._async_get_daily_means = fake_get_daily_means

    await sensor._async_replay_history()
    assert sensor.native_value == SEASON_SOMMAR
    assert sensor.extra_state_attributes["streak_count"] == 5

"""Sensor platform for SMHI Season."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import (
    CONF_TEMP_SENSOR,
    DOMAIN,
    REPLAY_LOOKBACK_DAYS,
    SEASON_HOST,
    SEASON_SOMMAR,
    SEASON_VAR,
    SEASON_VINTER,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor entity."""
    temp_sensor_id = entry.data[CONF_TEMP_SENSOR]
    async_add_entities([SMHISeasonSensor(entry, temp_sensor_id)], True)


class SMHISeasonSensor(RestoreEntity, SensorEntity):
    """Representation of the SMHI Meteorological Season Sensor."""

    _attr_icon = "mdi:weather-partly-snowy-rainy"

    def __init__(self, entry: ConfigEntry, temp_sensor_id: str) -> None:
        """Initialize the sensor."""
        self._entry = entry
        self._temp_sensor_id = temp_sensor_id
        self._attr_translation_key = "meteorological_season"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}_smhi_season"
        self._attr_device_class = SensorDeviceClass.ENUM
        self._state = SEASON_VINTER  # Default fallback
        self._streak = 0
        self._streak_target_season = None
        self._season_start_date = None
        self._daily_temps: dict[str, float] = {}

    @property
    def native_value(self) -> str:
        """Return current season."""
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra state attributes."""
        return {
            "streak_count": self._streak,
            "target_season": self._streak_target_season,
            "season_start_date": self._season_start_date,
            "monitored_sensor": self._temp_sensor_id,
        }

    async def async_added_to_hass(self) -> None:
        """Restore state on startup, catch up history, and attach midnight listener."""
        await super().async_added_to_hass()

        saved_state = await self.async_get_last_state()
        if saved_state:
            self._state = saved_state.state
            attrs = saved_state.attributes
            self._streak = attrs.get("streak_count", 0)
            self._streak_target_season = attrs.get("target_season")
            self._season_start_date = attrs.get("season_start_date")

        # Register so the manual recompute service can reach this entity.
        self.hass.data.setdefault(DOMAIN, {}).setdefault("entities", {})[
            self._attr_unique_id
        ] = self

        # Recompute the season from recorded history so backfilled/corrected
        # data (e.g. replacing a long -30 period) is reflected immediately,
        # instead of only catching up one day at a time going forward.
        await self._async_replay_history()
        self.async_write_ha_state()

        # Run evaluation every day at midnight (00:00:05)
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._async_daily_update, hour=0, minute=0, second=5
            )
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unregister from the recompute service map."""
        entities = self.hass.data.get(DOMAIN, {}).get("entities")
        if entities:
            entities.pop(self._attr_unique_id, None)
        await super().async_will_remove_from_hass()

    async def _async_daily_update(self, now: datetime) -> None:
        """Evaluate yesterday's average temperature against SMHI rules."""
        yesterday = (now - timedelta(days=1)).date()

        # Calculate daily mean from history stats or sensor state
        daily_mean = await self._async_get_yesterday_mean_temp(yesterday)
        if daily_mean is None:
            _LOGGER.warning(
                "Could not compute daily mean temperature for %s", yesterday
            )
            return

        # SMHI Rule: Round daily mean to 1 decimal place
        daily_mean = round(daily_mean, 1)
        _LOGGER.info("Yesterday (%s) mean temp: %.1f°C", yesterday, daily_mean)

        await self._evaluate_smhi_rules(yesterday, daily_mean)
        self.async_write_ha_state()

    async def _async_get_yesterday_mean_temp(self, target_date: date) -> float | None:
        """Fetch average temperature for given date using Home Assistant Recorder."""
        from homeassistant.components.recorder import get_instance
        from homeassistant.components.recorder.history import (
            state_changes_during_period,
        )

        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date, datetime.max.time())

        history = await get_instance(self.hass).async_add_executor_job(
            state_changes_during_period,
            self.hass,
            start_time,
            end_time,
            self._temp_sensor_id,
        )

        states = history.get(self._temp_sensor_id, [])
        valid_temps = []
        for s in states:
            try:
                valid_temps.append(float(s.state))
            except (ValueError, TypeError):
                continue

        if not valid_temps:
            return None

        return sum(valid_temps) / len(valid_temps)

    async def _evaluate_smhi_rules(
        self, current_date: date, temp: float, log: bool = True
    ) -> None:
        """Core state machine applying SMHI calendar rules and streak counts."""
        month = current_date.month
        day = current_date.day

        # Candidate determination
        candidate = None
        if temp <= 0.0:
            candidate = SEASON_VINTER
        elif 0.0 < temp < 10.0:
            # Spring allowed from Feb 15; Autumn allowed from Aug 1
            if self._state in (SEASON_VINTER, SEASON_VAR) and (
                month > 2 or (month == 2 and day >= 15)
            ):
                candidate = SEASON_VAR
            elif self._state in (SEASON_SOMMAR, SEASON_HOST) and (month >= 8):
                candidate = SEASON_HOST
        elif temp >= 10.0:
            candidate = SEASON_SOMMAR

        if candidate is None:
            self._streak = 0
            self._streak_target_season = None
            return

        # Check streaks
        required_days = 7 if candidate == SEASON_VAR else 5

        if candidate == self._streak_target_season:
            self._streak += 1
        else:
            self._streak_target_season = candidate
            self._streak = 1

        # Check if season transition threshold met
        if self._streak >= required_days and self._state != candidate:
            self._state = candidate
            start_date_calc = current_date - timedelta(days=required_days - 1)
            self._season_start_date = start_date_calc.isoformat()
            if log:
                _LOGGER.info(
                    "Season shifted to %s starting retroactively on %s",
                    candidate,
                    self._season_start_date,
                )

    async def _async_get_daily_means(
        self, start_date: date, end_date: date
    ) -> dict[str, float]:
        """Fetch mean temperature per calendar day from the recorder."""
        from homeassistant.components.recorder import get_instance
        from homeassistant.components.recorder.history import (
            state_changes_during_period,
        )

        start_time = datetime.combine(start_date, datetime.min.time())
        end_time = datetime.combine(end_date, datetime.max.time())

        history = await get_instance(self.hass).async_add_executor_job(
            state_changes_during_period,
            self.hass,
            start_time,
            end_time,
            self._temp_sensor_id,
        )

        states = history.get(self._temp_sensor_id, [])
        daily: dict[date, list[float]] = {}
        for s in states:
            try:
                temp = float(s.state)
            except (ValueError, TypeError):
                continue
            day = dt_util.as_local(s.last_updated).date()
            daily.setdefault(day, []).append(temp)

        return {
            d.isoformat(): round(sum(values) / len(values), 1)
            for d, values in daily.items()
        }

    async def _async_replay_history(self, days: int = REPLAY_LOOKBACK_DAYS) -> None:
        """Recompute season state by replaying recorded daily means.

        This makes backfilled/corrected history take effect: instead of only
        advancing one day at a time from the current (possibly stale) state, we
        walk the last ``days`` of recorded temperatures in order and re-run the
        same streak logic, arriving at the correct current season.
        """
        today = dt_util.now().date()
        end = today - timedelta(days=1)  # yesterday
        start = end - timedelta(days=days - 1)

        try:
            daily_means = await self._async_get_daily_means(start, end)
        except Exception:  # noqa: BLE001 - recorder not ready / unavailable
            _LOGGER.warning(
                "Could not replay temperature history; keeping current state"
            )
            return

        # Re-derive from scratch. Starting from winter and replaying forward is
        # sufficient because the lookback spans a full winter->summer cycle,
        # so by the time autumn arrives the state is already correct.
        self._state = SEASON_VINTER
        self._streak = 0
        self._streak_target_season = None
        self._season_start_date = None

        for offset in range(days):
            day = start + timedelta(days=offset)
            temp = daily_means.get(day.isoformat())
            if temp is None:
                # No reading for this day: mirror the daily-update behavior and
                # leave the streak untouched rather than breaking it.
                continue
            await self._evaluate_smhi_rules(day, temp, log=False)

    async def async_recompute(self) -> None:
        """Manually recompute the season (e.g. after backfilling history)."""
        await self._async_replay_history()
        self.async_write_ha_state()

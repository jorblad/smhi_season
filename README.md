# SMHI Meteorological Season

A [Home Assistant](https://www.home-assistant.io/) integration that calculates
the current **meteorological season** (according to
[SMHI](https://www.smhi.se/)) from an outdoor temperature sensor you already
have. It models the Swedish definition of the seasons rather than the calendar
dates.

| State      | English | Trigger |
| ---------- | ------- | ------- |
| `vinter`   | Winter  | Default / daily mean ≤ 0 °C |
| `var`      | Spring  | 7 consecutive days with 0 °C < mean < 10 °C (from Feb 15) |
| `sommar`   | Summer  | 5 consecutive days with mean ≥ 10 °C |
| `host`     | Autumn  | 7 consecutive days with 0 °C < mean < 10 °C (from Aug 1, when coming from summer) |

The sensor is an `enum` sensor whose `native_value` reflects the live season.
Transitions are applied **retroactively**: the season is considered to have
started on the first day of the qualifying streak.

## Installation

### HACS (recommended)

1. Open HACS → **Integrations** → ⋮ → **Custom repositories**.
2. Add `https://github.com/jorblad/smhi_season` with category **Integration**.
3. Search for **SMHI Meteorological Season** and install it.
4. Restart Home Assistant.

### Manual

Copy `custom_components/smhi_season/` into your Home Assistant
`config/custom_components/` directory and restart.

## Configuration

Go to **Settings → Devices & Services → Add Integration → SMHI Meteorological
Season** and pick the outdoor temperature sensor to monitor. That's it — the
sensor updates automatically every day at midnight (local time) using the
previous day's mean temperature from the recorder.

### Attributes

The sensor exposes useful diagnostics as attributes:

| Attribute           | Description |
| ------------------- | ----------- |
| `streak_count`      | How many consecutive days the current candidate season has been observed. |
| `target_season`     | The season the current streak is building towards (`null` if none). |
| `season_start_date` | ISO date the current season is considered to have started (first day of the streak). |
| `monitored_sensor`  | The entity ID of the temperature sensor being used. |

## Backfilling history

The integration normally advances **one day at a time** from the day it was
added. If you later correct or backfill temperature history (for example to fix
a bad sensor reading, or to seed a fresh install with past data), the season is
recomputed automatically on the next restart.

You can also trigger a recompute on demand without restarting, using the
`smhi_season.recompute` service — handy after backfilling via the helper script:

```yaml
service: smhi_season.recompute
```

The included `scripts/inject_history.py` injects daily temperatures directly
into the Home Assistant recorder database for testing/backfilling:

```bash
python scripts/inject_history.py
```

Edit `SENSOR_ENTITY_ID` / `DB_PATH` and the `temp_list` at the bottom of the
script to match your setup, then call the `smhi_season.recompute` service (or
restart) to apply it.

## Development

This is a HACS custom component. The deliverable is the
`custom_components/smhi_season/` package, validated by Hassfest and HACS.

Prerequisites (or just use the provided devcontainer):

```bash
pip install -r requirements-dev.txt
```

Checks — the same ones CI runs:

```bash
ruff check .
ruff format --check .
pytest tests/
```

`asyncio_mode` is set to `auto` in `pyproject.toml`, so sensor tests do not need
explicit event-loop markers.

## Releasing

Releases are fully automated by `.github/workflows/release.yml` and driven by
[Conventional Commits](https://www.conventionalcommits.org):

- A PR merged to `main` carrying a `major`, `minor`, or `patch` label cuts a
  release. The workflow bumps the `version` in `manifest.json`, tags `vX.Y.Z`,
  and writes a categorized changelog from the merged commits.
- You can also run the workflow manually (workflow dispatch) and pick the bump.
- Every merged PR gets an automatic **Release Notes** comment.
- Never bump the version or tag by hand — let the workflow do it.

## License

MIT — see [LICENSE](LICENSE).

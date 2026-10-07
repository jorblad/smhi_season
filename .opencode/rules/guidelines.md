# smhi_season — LLM working guidelines

A HACS custom component (Home Assistant integration). Deliverable is the
`custom_components/smhi_season/` package, validated by Hassfest + HACS, versioned
via `manifest.json`.

## Workflow

- Never commit/push to `main`. Use short-lived branches:
  `feat/...`, `fix/...`, `chore/...`, `docs/...`, `refactor/...`, `test/...`.
- Base off `origin/main`; one logical change per PR.
- Open PRs against `main` (`gh pr create --base main --head <branch>`) with
  Summary / What changed / Test plan.
- Confirm a PR is still open before pushing to its branch; merged branches are
  closed for new work.

## Commits

- Conventional Commits: `<type>(<scope>): <subject>`, imperative, lowercase,
  no trailing period. Types: feat, fix, docs, style, refactor, perf, test,
  build, ci, chore, revert. Use `feat`/`fix` so release notes categorize.
- Stage only intended files; review `git status` / `git diff` first.

## Pre-PR checks (CI mirrors these)

- `ruff check .` and `ruff format --check .`
- `pytest tests/`

## Tests

- Update/add tests when behavior changes (season transition rules, streak
  logic, config flow, error handling, translations). Don't skip to go green.

## Code conventions

- Public constants in `const.py`; user-facing strings as translation keys under
  `translations/`.
- Config flow declarative; surface errors via the `errors` dict.
- Sensor uses `SensorDeviceClass.ENUM`; `native_value` must be a plain
  `@property` (live state, not cached).
- Keep changes minimal; never commit secrets.

## Releases

- Cut by `.github/workflows/release.yml` when a merged PR has a `major`/`minor`/
  `patch` label (or manual dispatch). It bumps `manifest.json` version, tags
  `vX.Y.Z`, and writes a categorized changelog from conventional commits.
- Never bump versions or tag by hand.

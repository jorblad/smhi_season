# AGENTS.md — Development conventions for LLM-assisted work

These rules keep automated (LLM) and human changes to the **smhi_season** Home
Assistant integration consistent. Follow them for every task unless the user
explicitly overrides. This project is a HACS custom component, not a
standalone app: the deliverable is the `custom_components/smhi_season/` package,
validated by Hassfest and HACS, and versioned through `manifest.json`.

## Branching & pull requests

- **Never commit or push directly to `main`.** Always work on a short-lived
  feature branch.
- **Branch naming:** `feat/<kebab-description>`, `fix/...`, `chore/...`,
  `docs/...`, `refactor/...`, `test/...`. Use a descriptive, lowercase slug.
- **One logical change per branch/PR.** Don't mix unrelated work (e.g. a sensor
  rule fix and a docs change) unless the user asks for it explicitly.
- **Base off `origin/main`** (run `git fetch origin main` first). If a related
  change is already merged to `main`, do **not** re-include it in a new PR.
- **Open PRs against `main`** with `gh pr create --base main --head <branch>`
  (or the hosting UI). Every PR needs:
  - a concise title,
  - a description with *Summary*, *What changed*, and *Test plan*,
  - any caveats (e.g. depends on another open PR).
- **Check a PR is still open before pushing to its branch.** If you want to add
  a follow-up change, first confirm the branch's PR hasn't been merged/closed
  (e.g. `gh pr view -H <branch> --json state`). Once a PR is merged its branch
  is closed for new work — **create a new branch off `origin/main`** for the
  follow-up and open a new PR.
- Reference the originating request/issue when relevant.

## Commits

- **Follow [Conventional Commits](https://www.conventionalcommits.org).** Format
  is `<type>(<scope>): <subject>` (scope optional), e.g.
  `feat(sensor): add autumn transition rule`,
  `fix(config_flow): default errors to empty dict`,
  `chore(release): v1.2.2`. The subject is imperative, lowercase, and has no
  trailing period.
- **Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`,
  `build`, `ci`, `chore`, `revert`. Use `feat` / `fix` so release notes
  categorize correctly (see Releases).
- **Stage only intended files.** Always review `git status` and `git diff`
  before committing. Never commit secrets, `.env`, or credentials.
- Don't commit build artifacts or generated files (`__pycache__/`, `.venv/`,
  `.pytest_cache/` are gitignored already).
- Prefer small, reviewable commits. Don't force-push shared branches unless
  asked.

## Before committing / opening a PR

Run the same checks CI runs so PRs are green:

- Lint: `ruff check .` and `ruff format --check .`
- Tests: `pytest tests/`

If you cannot run a check locally, say so and note it in the PR.

## Testing

- **Update tests when behavior changes.** If a change alters existing behavior
  (season transition rules, streak logic, config flow, error handling, or
  translations), update the affected tests in `tests/` so they assert the *new*
  behavior. A change that breaks CI tests without updating them is incomplete —
  fix or update the tests, don't skip/disable them to go green.
- **Tests for every rule.** Every meteorological-season transition (vinter →
  vår, vår → sommar, sommar → höst, höst → vinter) and the config flow path
  must have test coverage. Add a workflow's tests in the same PR as the feature.
- Run `pytest tests/` before opening a PR and resolve failures.

## Code conventions

- Match existing style. Reuse existing libraries/utilities; don't add new
  dependencies without a reason.
- **Layout:** business logic lives in `custom_components/smhi_season/`. Public
  constants (seasons, config keys) go in `const.py`; never hardcode them inline.
  User-facing strings use translation keys under `translations/`.
- **Config flow:** keep `config_flow.py` declarative; surface validation errors
  through the form's `errors` dict rather than raising.
- **Device class:** the sensor uses `SensorDeviceClass.ENUM`; `native_value`
  must reflect live state (use a plain `@property`, not a cached one).
- Keep changes minimal; avoid unrelated refactors in the same PR.
- Never log or commit secrets; use `const.py` / config entries for config.

## Releases

- Releases are produced by `.github/workflows/release.yml`. A release is cut when
  a PR merged to `main` carries a `major` / `minor` / `patch` label (or by
  running the workflow manually with a bump choice).
- The workflow bumps the `version` field in
  `custom_components/smhi_season/manifest.json`, tags `vX.Y.Z`, and generates a
  categorized changelog (Features, Bug Fixes, Breaking Changes, Dependencies,
  Other) **from the merged Conventional Commits**. Write commit messages
  accordingly so the notes are accurate.
- Every merged PR also gets an automatic "Release Notes" comment summarizing its
  conventional commits.
- **Don't bump versions or cut releases by hand** — let the workflow do it once
  the PR is labeled and merged. HACS picks up the new `manifest.json` version
  automatically.

## General

- Confirm the task scope before large changes. When unsure about behavior,
  design, or HA conventions, ask rather than guessing.
- After implementing, verify with tests/lint before reporting done.

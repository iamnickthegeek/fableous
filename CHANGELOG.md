# Changelog

## v6.1.0

- Formalised the Fable trigger decision into a short checklist in `SKILL.md`.
- Added "When to Use It" section to `README.md`.

## v6.0.0

- Native-first rewrite. Removed the Python engine, daemon, and SQLite state.
- Uses only native Hermes tools: `todo`, `delegate_task`, `terminal`, `cronjob`, `session_search`, `memory`.
- Added mandatory model verification, cross-family verification, dynamic replanning, and strict 6-stage procedure.
- Added helper scripts: `verify_models.py`, `auto_detect_providers.py`, `run_stage.py`, `fable_routing.py`.
- Added non-technical `INSTALL.md`, `setup.sh`, and updated `README.md`.
- Archived legacy v1-v5 code in `archive/`.

## Earlier versions

See `archive/v5-engine/CHANGELOG.md` for v1-v5 history.

# v5 Test Suite

Automated test coverage for the Fable Engine v5 core components.

## Running the Tests

```bash
cd ~/.hermes/skills/fable-orchestrator
python3 -m pytest tests/ -v
```

All 10 tests pass. The test suite covers the two most critical engine components: `state.py` (persistence) and `planner.py` (dynamic DAG).

## Test Coverage

### `tests/test_state.py` (4 tests)

**`test_create_and_get_task`** 
- Verifies `StateManager.create_task()` creates a task with the correct ID prefix
- Verifies `get_task()` returns the task with all fields (id, status, description, clarified_description)
- Verifies `get_stages()` returns all stages in the correct order
- Validates the `stage_name` vs `name` key fallback works (uses both `stage_name` and `name` in input dicts)

**`test_stage_status_update`**
- Verifies `update_stage_status()` correctly writes status, model_used, provider_used, error_log, and result_summary
- Checks that completed stages are retrievable with all metadata

**`test_work_log`**
- Verifies `add_work_log()` creates entries with decisions, failures, and open_items
- Verifies `get_work_logs()` returns logs in reverse chronological order

**`test_task_status_lifecycle`**
- Verifies full lifecycle: `running` → `paused` → `running` → `completed`
- Verifies `mark_task_complete()` sets `final_output_path` (not `final_output` — see `v5-pitfalls.md` #5)

### `tests/test_planner.py` (6 tests)

**`test_get_model_for_stage`**
- Verifies `get_model_for_stage("research")` returns a valid primary model from the routing table
- Checks that model names are in the expected set and providers match

**`test_get_model_fallback`**
- Verifies `attempt=1` returns a fallback model containing "gemini"
- Verifies `attempt=2` returns a tertiary model containing "nemotron"
- Uses `assert "gemini" in model` instead of exact string matching (models may be renamed)

**`test_plan_stages_small_task`**
- Verifies `plan_stages()` returns at least one stage for a trivial task
- Uses structural assertions (len > 0) rather than exact stage lists (the planner is heuristic)

**`test_plan_stages_complex_task`**
- Verifies complex tasks include "plan" and "critique" stages
- These are the distinguishing features of complex vs simple task routing

**`test_get_ready_stages`**
- Verifies dependency resolution: only stages with all dependencies completed are returned
- Tests the parallel/sequential separation logic

**`test_is_complete`**
- Verifies `is_complete()` returns True when all stages are "completed"
- Verifies it returns False when any stage is still "pending"

## Key Testing Lessons

1. **Structural assertions over exact matches**: The planner is heuristic. Tests should assert properties (e.g., "has at least one stage") rather than exact sequences (e.g., "must have research"). This prevents false failures when the planner logic evolves.

2. **Model name partial matching**: Model names change (e.g., `gemini-2.5-flash-lite` might become `gemini-2.5-flash-lite-preview`). Use `assert "gemini" in model` instead of `assert model == "gemini-2.5-flash-lite"`.

3. **Column name consistency**: The SQLite schema uses `final_output_path`. Tests must reference this exact key. A mismatch between the schema and the test causes `KeyError`.

4. **Stage dict key fallback**: The `StateManager` must handle both `name` and `stage_name` in input dicts. Tests should verify this by passing mixed dicts.

## What Is Not Tested (Yet)

- `agent_pool.py` (parallel execution, subprocess spawning) — requires mocking `subprocess.run`
- `verification.py` (failable checks) — requires temporary files and mock URLs
- `core.py` (end-to-end orchestration) — requires a full integration test with mocked model calls
- `context.py` (context compression) — straightforward but needs a test with large files
- `questioner.py` (proactive questioning) — requires mocking the `hermes chat` subprocess

These are candidates for future test coverage. The critical path (state persistence + planning) is fully covered.

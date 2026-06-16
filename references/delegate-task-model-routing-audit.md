# delegate_task Model-Routing Source Audit — June 2026

## Finding

`delegate_task` has **no per-call `model` parameter**. The tool schema, dispatch function, and Python function signature all lack a `model` field. Model routing is resolved exclusively from `delegation.model` and `delegation.provider` in `config.yaml` — global settings that apply to ALL subagents.

## Evidence

### 1. Tool Schema — No model Property

File: `tools/delegate_tool.py`, lines 2815-2932 (`DELEGATE_TASK_SCHEMA`)

The schema defines parameters: `goal`, `context`, `toolsets`, `tasks`, `role`, `acp_command`, `acp_args`. There is no `model` parameter and no `provider` parameter. The model calling this tool has no way to specify which model a subagent should run on.

### 2. Dispatch — No Model Extraction

File: `run_agent.py`, lines 5127-5144 (`_dispatch_delegate_task`)

```python
def _dispatch_delegate_task(self, function_args: dict) -> str:
    from tools.delegate_tool import delegate_task as _delegate_task
    return _delegate_task(
        goal=function_args.get("goal"),
        context=function_args.get("context"),
        toolsets=function_args.get("toolsets"),
        tasks=function_args.get("tasks"),
        max_iterations=function_args.get("max_iterations"),
        acp_command=function_args.get("acp_command"),
        acp_args=function_args.get("acp_args"),
        role=function_args.get("role"),
        parent_agent=self,
    )
```

No `model` or `provider` extraction from `function_args`. Even if the model supplied `model` in the call, it would be silently dropped.

### 3. Function Signature — No Model Parameter

File: `tools/delegate_tool.py`, lines 2012-2022

```python
def delegate_task(
    goal: Optional[str] = None,
    context: Optional[str] = None,
    toolsets: Optional[List[str]] = None,
    tasks: Optional[List[Dict[str, Any]]] = None,
    max_iterations: Optional[int] = None,
    acp_command: Optional[str] = None,
    acp_args: Optional[List[str]] = None,
    role: Optional[str] = None,
    parent_agent=None,
) -> str:
```

No `model` parameter.

### 4. Model Resolution — Config Only

File: `tools/delegate_tool.py`, lines 2500-2611 (`_resolve_delegation_credentials`)

Model routing is resolved from `cfg.get("model")` and `cfg.get("provider")`, which come from `config.yaml`'s `delegation:` section. Lines 2573-2581:

```python
if not configured_provider:
    # No provider override — child inherits everything from parent
    return {
        "model": configured_model,     # None when delegation.model is empty
        "provider": None,               # None when delegation.provider is empty
        "base_url": None,
        "api_key": None,
        "api_mode": None,
    }
```

When both are None (the default, since `delegation.model: ''` and `delegation.provider: ''` in config), the child agent inherits the parent's model and provider.

### 5. Child Agent Construction — Fallback to Parent

File: `tools/delegate_tool.py`, line 1084

```python
effective_model = model or parent_agent.model
effective_provider = override_provider or getattr(parent_agent, "provider", None)
```

When `model` (from `creds["model"]`) is None, the child uses `parent_agent.model`. When `override_provider` (from `creds["provider"]`) is None, the child uses the parent's provider.

### 6. Config Defaults

File: `~/.hermes/config.yaml`

```yaml
delegation:
  model: ''
  provider: ''
```

Both are empty strings, which `_resolve_delegation_credentials` converts to None.

## Implications

- Any `model=` value passed in a `delegate_task` tool call is silently ignored.
- Every subagent runs on the parent session's model and provider.
- The `[MODEL: ...]` tag in stage prompts is self-reported and unverifiable.
- Cross-family verification via `delegate_task` is impossible.
- The only way to route a specific model for a stage is `terminal` with `hermes chat -q -m MODEL --provider PROVIDER`.

## Alternative Approaches

1. **Set `delegation.model` and `delegation.provider` globally** in `config.yaml` — forces ALL subagents to the same model. Useful for a single-stage rerun but defeats the routing table.

2. **Use `scripts/run_stage.py`** — wraps `hermes chat -q` with `-m` and `--provider` flags, automatic secondary/tertiary fallback, and model tag verification.

3. **Wait for Hermes to add per-call model routing** — the `delegate_task` tool schema would need `model` and `provider` properties, and the dispatch and function would need to thread them through to `_build_child_agent`. This would be a code change in `tools/delegate_tool.py`.
# Model-Mismatch Recovery in Fable v6

## When this applies

You asked `delegate_task` to run a stage on a specific model, the subagent’s output begins with the correct `[MODEL: name, PROVIDER: provider]` tag, but the subagent’s metadata says it actually ran on a different model. This most often hits Stage 4 (Verify) and Stage 5 (Critique), where cross-family separation is mandatory.

## Why it happens

`delegate_task` treats the `model` parameter as a suggestion. The subagent session can inherit the parent session’s default model or provider, even when the tag is present. Relying on the tag alone is not enough when the tool metadata contradicts it.

## Recovery recipe

Do not accept the contradictory output. Re-run the stage through the terminal with hardcoded model and provider flags so Hermes cannot ignore the assignment.

```bash
hermes chat -q 'STAGE_PROMPT' \
  -m deepseek-v4-pro \
  --provider opencode-go \
  -Q \
  -t web,terminal,file
```

Replace the model/provider with the one required by the routing table for that stage. For example:

- Stage 4 (Verify): `-m deepseek-v4-pro --provider opencode-go`
- Stage 5 (Critique): `-m glm-5.1 --provider opencode-go`

## What to pass as the prompt

Read the subagent’s prior output into the terminal prompt, or write a focused re-verification prompt. Example for a failed Verify stage:

```
Read /path/to/stage4_verification.md and the generated lead sheets.
Confirm the verification checks are sound and the outputs are internally consistent.
Report pass/fail and any concerns.
At the top of your response write exactly: [MODEL: deepseek-v4-pro, PROVIDER: opencode-go].
```

## Log it

Append a note to `WORK_LOG.md` recording:
- Intended model.
- Actual model reported by subagent metadata.
- That recovery was run via terminal.
- Final verified model.

This preserves the audit trail and prevents the mismatch from being forgotten across sessions.

## Prevention

For Verify and Critique, consider using the terminal method as the primary execution path if `delegate_task` has already shown it cannot honor model assignments in your current environment. The small extra cost is cheaper than a silently cross-contaminated verification.

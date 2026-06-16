# v6.1 Trigger Checklist

Fable v6.1 formalises when to invoke the orchestrator. The skill itself is
powerful but not free. Use this checklist before starting a Fable run.

## Trigger if YES to any of these

1. **Explicit request** — the user asked for thorough/systematic/Fable mode:
   - "do this thoroughly"
   - "be systematic"
   - "deep work mode"
   - "run this through fable"
   - similar explicit cues
2. **Multi-part scope** — the task spans multiple files, sources, sessions,
   domains, or deliverables.
3. **High miss risk** — a one-shot attempt would plausibly miss something
   important.

## Also consider triggering if

4. **Verification/critique value** — there is more than one valid approach, or
   the output benefits from independent cross-checking.

## Skip Fable if

- The task has one obvious approach.
- It clearly fits in a single pass.
- None of the above conditions apply.

## Rule of thumb

When in doubt, trigger Fable. The cost of running Fable on a slightly simple
task is lower than the cost of skipping Fable on a task that needed it.

## Why this was formalised

Prior to v6.1 the trigger was described informally. The checklist removes
ambiguity for the agent and prevents both under-use (skipping Fable on hard
work) and over-use (running Fable on trivial one-shot tasks).

# What Claude Fable Actually Is, vs What Kimi 2.6 Built

## The Original Fable Concept

Fable started as a *mode of operation* within Claude Code before it became a model (Fable 5). The core idea was not "use a smarter model" — it was **structural discipline imposed on how a model works**:

- **Long-horizon autonomy**: Work across days, not minutes. Maintain context across sessions without human hand-holding.
- **Dynamic parallel sub-agent orchestration**: Spin up hundreds of parallel subagents, each working on a slice of the problem, then aggregate results.
- **Self-verification**: The model writes its own tests, uses vision to check outputs against the original design, and corrects itself before presenting to the user.
- **Proactive behavior**: Ask clarifying questions before starting, anticipate obstacles, and re-plan when assumptions break.
- **Minimal oversight**: The user hands off a goal and reviews completed work, not every step.
- **Context compression**: Intelligent decisions about what to keep and what to discard, rather than dumping everything into context.
- **Asynchronous execution**: The agent runs while the user is offline and delivers results when done.

## What Kimi 2.6 Built (v1-v3)

Kimi 2.6 correctly identified the core insight: **the value is the loop, not the model**. The skill it built captures:

- **Staged execution discipline**: 6-stage loop (Research → Plan → Implement → Verify → Critique → Consolidate)
- **Cross-family verification**: Different models for implementation vs verification/critique (the anti-hallucination measure)
- **Fail-open routing**: Fallback chains when models/providers are exhausted
- **Consolidation stage**: Fixes from verification are propagated to the final deliverable (the most important structural fix)
- **Prompt guardrails**: Mandatory instructions injected into every stage
- **Work logs**: Continuity mechanism for multi-session tasks
- **Model switching workaround**: Discovered that `delegate_task(model=...)` is suggestive, not enforcing; built a subprocess-based workaround

## What Kimi 2.6 Missed

### 1. Sequential execution only
The v3 script runs stages 1→2→3→4→5→6 in strict sequence. Real Fable runs independent stages in parallel. Research and Plan have no dependency on each other — they should run concurrently. The skill even says "delegate to the right model for each stage" but the implementation never actually does this in parallel.

### 2. No checkpoint / resume
If the process is interrupted (session reset, machine reboot, token limit), the v3 script starts from scratch. Real Fable persists state and resumes. The skill mentions work logs but doesn't actually use them to resume execution.

### 3. No dynamic planning
Every task runs the same 6-stage loop regardless of whether it needs it. A pure coding task might skip research. A data analysis task might need an extra cleaning stage. The v3 script is rigid.

### 4. No context compression
The v3 script passes full file contents to each stage. For a 6-stage research task with long outputs, this could exceed context windows or waste tokens. Real Fable intelligently summarizes what each stage needs.

### 5. No self-monitoring of the orchestration itself
The v3 script spawns `hermes chat -q` processes but doesn't track PIDs, handle zombie processes, or detect if a subprocess hung. Real Fable monitors its sub-agents.

### 6. No proactive questioning
The v3 script takes the task string and runs. Real Fable asks clarifying questions before committing to a plan.

### 7. No vision integration
Real Fable uses vision to check outputs (e.g., does the generated HTML match the design mockup?). The v3 skill has no vision capability at all.

### 8. The subprocess workaround is fragile
Spawning `hermes chat -q` for every stage creates independent processes that can't share the current session's context. The subagent starts cold each time. Real Fable's subagents share context through a structured state store.

## What v4 Implements

- **Parallel execution**: Independent stages (identified by Stage 0 planner) run concurrently via threads
- **Checkpoint / resume**: `state.json` persists after every stage. Run with `--resume` to continue after interruption
- **Dynamic stage planner**: Stage 0 analyzes the task and builds a custom DAG. Some tasks skip research; some add extra stages
- **Context pruning**: `summarize_file()` limits dependency inputs to ~100 lines (head + tail + omission count)
- **Self-healing retries**: Failed stages automatically retry with the secondary model
- **Process tracking**: Background execution mode with PID tracking
- **Dependency graph execution**: Stages only run when all dependencies are satisfied, enabling true parallel execution

## What v4 Still Can't Do (Hermes Constraints)

- **True asynchronous execution**: Hermes sessions are synchronous. We can't "hand off and review later" without a cron job
- **Vision-based verification**: Hermes has vision tools but integrating them into the automated loop requires manual coordination
- **Hundreds of parallel agents**: Hermes `delegate_task` has concurrency limits (3 for this user). The v4 script uses threading + subprocess, which is bounded by the machine's resources, not Hermes' limits
- **Cross-session context**: Hermes sessions reset daily. The state.json survives, but the orchestrator must be re-triggered manually
- **Dynamic re-planning mid-flight**: The v4 planner runs once at the start. Real Fable re-plans when it encounters obstacles

## Verdict

Kimi 2.6 built a solid **procedural scaffold** that captures the *discipline* of Fable. The v3 skill is genuinely useful for tasks that fit the 6-stage loop. What's missing is the *runtime infrastructure* that makes Fable autonomous: parallelism, checkpointing, dynamic planning, and context management.

v4 closes the parallelism and checkpointing gaps. The remaining gaps (vision, async, hundreds of agents) are bounded by the Hermes runtime, not the skill design.

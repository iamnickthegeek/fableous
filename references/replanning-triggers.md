# Replanning Triggers — v0.6.0

Dynamic replanning is a core feature of the Fable Orchestrator v0.6.0. The orchestrator MUST check for replanning triggers after every stage completion. If a trigger fires, the orchestrator MUST rebuild the plan.

## Trigger Conditions

| ID | Trigger | Condition | Action |
|----|---------|-----------|--------|
| T1 | Insufficient research | Research found fewer than 3 sources | Add "Extended Research" stage. Or skip to Plan if user provided data. |
| T2 | Task simpler than expected | Plan reveals task can be done in fewer stages | Skip unnecessary stages. Update todo list. |
| T3 | Task more complex than expected | Plan reveals task needs additional stages | Add new stages (e.g., "Architecture Review", "Security Audit", "Performance Test"). Update todo list. |
| T4 | Implementation diverged from plan | Implement produces fundamentally different output than planned | Rebuild Plan from scratch. Preserve completed Research. |
| T5 | Verification failed | Tests fail, sources broken, consistency errors | Re-run Implement or add "Fix" stage before Critique. |
| T6 | Critical weaknesses found | Critique finds more than 3 critical weaknesses | Add "Fix" stage before Consolidate. |
| T7 | New requirements | User provides new requirements mid-flight | Rebuild Plan. Preserve completed stages. |
| T8 | Model verification exhausted | Model verification fails 3 times | Add "Model Fallback" note to work log. Use cheapest available model. |
| T9 | Budget constraint | User indicates budget is limited | Skip expensive models. Use cheaper alternatives. Flag trade-offs. |
| T10 | Time constraint | User indicates deadline is near | Skip non-critical stages. Prioritize core deliverable. |

## Replanning Procedure

When ANY trigger fires, follow this exact procedure:

### Step 1: Halt execution

Do NOT proceed to the next stage. Stop immediately.

### Step 2: Log the trigger

Append to the work log:
```markdown
## Replanning Event — [YYYY-MM-DD HH:MM]
- Trigger: [T#] — [Description]
- Current plan: [list of stages]
- Completed stages: [list]
- Obstacle: [what changed]
```

### Step 3: Analyze the gap

Use `delegate_task` with a "replanning analysis" prompt:

```
You are the Fable Orchestrator replanning engine.

Analyze the obstacle:
- Original plan: [plan]
- Completed stages: [list]
- Current stage: [stage]
- Obstacle: [obstacle]
- Work log: [work log]

Questions:
1. Which completed stages are still valid?
2. Which stages must be modified?
3. Which new stages must be added?
4. Which stages can be removed?
5. What are the new dependencies?

Return your analysis as a brief report.
```

### Step 4: Build the new plan

Use `delegate_task` with a "replanning" prompt:

```
You are the Fable Orchestrator replanning engine.

Rebuild the stage plan. Rules:
- Preserve completed work. Do NOT re-run completed stages.
- Add new stages only if necessary.
- Remove stages that are no longer needed.
- Update dependencies.
- Maintain the 6-stage structure where possible.
- Return a JSON todo list with these fields: id, content, status, depends_on.

Original plan: [plan]
Completed stages: [list]
Obstacle: [obstacle]
Analysis: [analysis from Step 3]
```

### Step 5: Update the todo list

Use `todo(merge=true)` to update the existing todo list with the new stages.

### Step 6: Update the work log

Append the new plan to the work log:
```markdown
## Replanning Result — [YYYY-MM-DD HH:MM]
- New plan: [list of stages]
- New dependencies: [list]
- Reason: [why the plan changed]
```

### Step 7: Continue execution

Resume execution with the new plan. Start with the next pending stage.

## Replanning Prompt Template

Stored in `templates/replanning-prompt.md`:

```markdown
You are the Fable Orchestrator replanning engine.

The current task has encountered an obstacle:
- Original plan: [plan]
- Completed stages: [list]
- Current stage: [stage]
- Obstacle: [obstacle]
- Work log: [work log]

Rebuild the stage plan. Rules:
- Preserve completed work. Do NOT re-run completed stages.
- Add new stages only if necessary.
- Remove stages that are no longer needed.
- Update dependencies.
- Maintain the 6-stage structure where possible.
- Return a JSON todo list with these fields: id, content, status, depends_on.
```

## Examples

### Example 1: T1 — Insufficient Research

**Trigger:** Research stage found only 2 competitors instead of the required 3.

**Action:**
1. Add "Extended Research" stage before Plan.
2. Update todo list.
3. Continue with Extended Research.

### Example 2: T5 — Verification Failed

**Trigger:** Verify stage found 2 broken URLs and 1 factual error.

**Action:**
1. Add "Fix" stage after Verify.
2. Fix stage: delegate to Implement model to fix the errors.
3. Re-run Verify after Fix.
4. If Verify passes, continue to Critique.

### Example 3: T7 — New Requirements

**Trigger:** User says "Actually, I need this for a technical audience, not executives."

**Action:**
1. Rebuild Plan with technical audience segmentation.
2. Preserve completed Research.
3. Re-run Plan and Implement with new audience.
4. Re-run Verify, Critique, Consolidate.

### Example 4: T3 — Task More Complex

**Trigger:** Plan reveals the task requires a database schema, API design, and frontend — originally thought to be just a landing page.

**Action:**
1. Add "Database Design" stage after Plan.
2. Add "API Design" stage after Database Design.
3. Update dependencies: Implement now depends on Database Design and API Design.
4. Continue with Database Design.

## Replanning Checklist

Before declaring a replanning event complete:

- [ ] Did you halt execution immediately?
- [ ] Did you log the trigger in the work log?
- [ ] Did you analyze the gap?
- [ ] Did you build a new plan?
- [ ] Did you update the todo list?
- [ ] Did you preserve completed stages?
- [ ] Did you update the work log with the new plan?
- [ ] Did you continue execution with the new plan?

**Do NOT skip the replanning procedure.** If a trigger fires, you MUST replan.

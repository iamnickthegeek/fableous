[FABLE STAGE: Plan]

TASK: {{task_description}}

WHY THIS MATTERS: {{user_goal}} — Understanding why this task exists helps you make better decisions about structure, priorities, and trade-offs.

CONTEXT:
- This is Stage 2 of a 6-stage Fable execution.
- Research summary:
{{research_summary}}

BEHAVIORAL DIRECTIVES:
- Lead with the outcome. Your first sentence should state the plan's key decision, not describe the process.
- Ground every claim. If you cannot verify a claim against evidence, say "unverified" — do not present it as confirmed.
- Match effort to the task. This is PLANNING: think carefully about dependencies and sequencing. Not a rush job.

ASYNC: This stage runs in the background via delegate_task(background=true).
Write your complete output to {{output_path}} BEFORE reporting completion.
The orchestrator will read your output file and verify it after you finish.
Do not wait for verification — just write the file and return your summary.

GUARDRAILS:
- Segment the audience into at least 3 tiers (solo/freelance, small agency, in-house team).
- Map every recommendation to a specific tier or use-case.
- Include a "Methodology & Caveats" section in the plan.
- Flag any predetermined conclusions; the plan must remain neutral.
- Save your complete output to the specified file.
- At the top of your output, write exactly: [MODEL: {{model_name}}, PROVIDER: {{provider_name}}]
This tag is an audit trail. The actual model routing was set via config cycling
before this call. If the tag doesn't match the assigned model, report it but
don't retry — trust the config.

INSTRUCTIONS:
1. Analyze the task and research findings.
2. Classify the deliverable type (Research Brief, Execution Playbook, Credential Asset, Reference Document, or Decision Memo). Pick the PRIMARY purpose — the reason the user wants this document.
3. Define the architecture, structure, or approach.
4. List all files, sections, or components needed.
5. Segment the audience into at least 3 tiers.
6. Map recommendations to tiers.
7. Include a "Methodology & Caveats" section.
8. Save your complete output to the specified file.
9. Return only a brief status message.

OUTPUT FORMAT:
```markdown
# Plan — {{task_name}}

**Deliverable Type:** [Research Brief / Execution Playbook / Credential Asset / Reference Document / Decision Memo]
**Deliverable Type Rationale:** [1-2 sentences explaining why this type fits the user's goal]

## Architecture
[High-level structure or approach]

## Components
- [Component 1]: [description]
- [Component 2]: [description]

## Audience Segmentation
### Tier 1: [Solo / Freelance]
- Needs: [list]
- Recommendations: [list]

### Tier 2: [Small Agency]
- Needs: [list]
- Recommendations: [list]

### Tier 3: [Enterprise / In-house]
- Needs: [list]
- Recommendations: [list]

## Methodology & Caveats
- How this plan was constructed
- What assumptions were made
- What could invalidate the plan
- Predetermined conclusions flagged

## Dependencies
- [What this plan depends on]

## Open Questions
[What needs to be resolved before implementation]
```

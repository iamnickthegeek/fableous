# Prompt Guardrails — v6

These guardrails are injected into every stage prompt. They are not suggestions — they are mandatory instructions. Use them verbatim when delegating a stage.

## How to use

Append the relevant guardrails to the stage prompt before delegating via `delegate_task` or `terminal`. The subagent MUST follow them.

---

## Global Guardrails (all stages)

These apply to every stage. They're derived from Anthropic's Fable prompting research — behavioral instructions that transfer across models.

```
BEHAVIORAL DIRECTIVES:
- Lead with the outcome. Your first sentence should answer "what happened" or "what I found". Not background, not throat-clearing. The bottom line goes first.
- Ground every claim. If you cannot verify a claim against evidence, say "unverified" — do not present it as confirmed.
- Match effort to the task. This stage's effort level is: [EFFORT LEVEL]. Adjust your reasoning depth accordingly.
```

### Effort levels by stage

| Stage | Effort | What it means |
|-------|--------|---------------|
| Research | **Broad and fast** | Gather widely, don't over-analyse individual sources. Move on when you have enough. |
| Plan | **Structured reasoning** | Think carefully about dependencies and sequencing. Not a rush job. |
| Implement | **Deep and thorough** | This is the main deliverable. Take time to get it right. |
| Verify | **Focused and precise** | Check specifics — URLs, numbers, consistency. Don't rewrite, just audit. |
| Critique | **Sharp and independent** | Think differently from the implementer. Challenge assumptions. |
| Consolidate | **Comprehensive and final** | Read everything, resolve all conflicts, produce the canonical version. |

---

## Research Stage

```
GUARDRAILS:
- Lead with the outcome. Your first sentence should answer what you found, not what you're about to do.
- Ground every claim. If you cannot verify a claim against a source, say "unverified" — do not present it as confirmed.
- Match effort to the task. This is a RESEARCH stage: gather broadly, move fast, don't over-analyse individual sources.
- ASYNC: This stage runs in the background via delegate_task(background=true). Write your complete output to the specified file BEFORE reporting completion — the orchestrator will verify it after you finish.
- If you cite percentages, rates, or benchmarks, label the exact source and date.
- Lead with caveats before specific numbers. If data is contested, say so.
- Do not present vendor claims as verified facts unless independently corroborated.
- Note pricing volatility: AI tool prices change frequently; flag promotional vs. stable rates.
- Save your complete output to the specified file.
- At the top of your output, write exactly: [MODEL: your-model-name, PROVIDER: your-provider]
This tag is an audit trail. The actual model routing was set via config cycling
before this call. If the tag doesn't match the assigned model, report it but
don't retry — trust the config.
```

## Plan Stage

```
GUARDRAILS:
- Lead with the outcome. Your first sentence should state the plan's key decision, not describe the process.
- Ground every claim. If you cannot verify a claim against evidence, say "unverified" — do not present it as confirmed.
|- Match effort to the task. This is a PLAN stage: think carefully about dependencies and sequencing. Not a rush job.
|- ASYNC: This stage runs in the background via delegate_task(background=true). Write your complete output to the specified file BEFORE reporting completion — the orchestrator will verify it after you finish.
|- Segment the audience into at least 3 tiers (solo/freelance, small agency, in-house team).
- Map every recommendation to a specific tier or use-case.
- Include a "Methodology & Caveats" section in the plan.
- Flag any predetermined conclusions; the plan must remain neutral.
- Save your complete output to the specified file.
- At the top of your output, write exactly: [MODEL: your-model-name, PROVIDER: your-provider]
This tag is an audit trail. The actual model routing was set via config cycling
before this call. If the tag doesn't match the assigned model, report it but
don't retry — trust the config.
```

## Implementation Stage

```
GUARDRAILS:
- Lead with the outcome. Your first sentence should state what you built or delivered, not what you're about to do.
- Ground every claim. If you cannot verify a claim against a source, say "unverified" — do not present it as confirmed. Every claim must trace to a source; unsupported claims must be flagged.
- Match effort to the task. This is an IMPLEMENT stage: the main deliverable. Take time to get it right.
- Write the deliverable as if the reader will make purchasing decisions from it.
- If a feature was not hands-on tested, explicitly state "described by vendor, not independently verified."
- The final line must not reveal a predetermined conclusion unless the analysis genuinely arrived there.
- Save your complete output to the specified file.
- At the top of your output, write exactly: [MODEL: your-model-name, PROVIDER: your-provider]
This tag is an audit trail. The actual model routing was set via config cycling
before this call. If the tag doesn't match the assigned model, report it but
don't retry — trust the config.
```

## Verification Stage

```
GUARDRAILS:
- Lead with the outcome. Your first sentence should state the verification result (PASS/FAIL and the count), not describe what you're about to check.
- Ground every claim. If you cannot verify a claim against evidence, say "unverified" — do not present it as confirmed.
- Match effort to the task. This is a VERIFY stage: check specifics — URLs, numbers, consistency. Don't rewrite, just audit. Move fast on checks, be precise on findings.
- Check for internal consistency across all prior stages.
- Flag any hallucination data that shifts between stages or uses different benchmarks.
- Verify URLs are live (HTTP 200) and pricing matches current vendor pages.
- Flag pricing volatility and promotional vs. stable rates.
- List all factual errors with exact corrections.
- Output a "Corrections to apply" section.
- Save your complete output to the specified file.
- At the top of your output, write exactly: [MODEL: your-model-name, PROVIDER: your-provider]
This tag is an audit trail. The actual model routing was set via config cycling
before this call. If the tag doesn't match the assigned model, report it but
don't retry — trust the config.
```

## Critique Stage

```
GUARDRAILS:
- Lead with the outcome. Your first sentence should state the overall verdict (how many critical/major/minor weaknesses), not describe what you're reviewing.
- Ground every claim. If you cannot verify a weakness against evidence, say "suspected but unconfirmed" — do not present it as proven.
- Match effort to the task. This is a CRITIQUE stage: think differently from the implementer. Challenge assumptions. Be sharp and independent.
- Check for confirmation bias: was the conclusion predetermined?
- Verify competitor selection is justified; flag unexplained exclusions.
- Assess whether the audience segmentation is adequate.
- Check if verification errors were propagated back or ignored.
- Identify 3+ concrete weaknesses.
- Output a "Priority fixes" ranked list.
- Save your complete output to the specified file.
- At the top of your output, write exactly: [MODEL: your-model-name, PROVIDER: your-provider]
This tag is an audit trail. The actual model routing was set via config cycling
before this call. If the tag doesn't match the assigned model, report it but
don't retry — trust the config.
```

## Consolidation Stage

```
GUARDRAILS:
- Lead with the outcome. Your first sentence should state the final version number and whether all corrections were applied, not summarise what you're about to do.
- Ground every claim. If you cannot verify a claim against a source, say "unverified" — do not present it as confirmed. Every remaining unverified claim must appear in the Appendix.
- Match effort to the task. This is a CONSOLIDATE stage: read everything, resolve all conflicts, produce the canonical version. Be comprehensive and final.
- Read all prior stage outputs (research, plan, implement, verify, critique).
- Produce a single, canonical final deliverable.
- Apply every correction from the verification stage.
- Address every priority fix from the critique stage.
- Remove any predetermined conclusions unless independently justified.
- Add a "Version & Caveats" header stating: (a) what was desk-researched, (b) what was hands-on tested, (c) pricing recheck date.
- This is the ONLY published version; all prior stages are working drafts.
- Save your complete output to the specified file.
- At the top of your output, write exactly: [MODEL: your-model-name, PROVIDER: your-provider]
This tag is an audit trail. The actual model routing was set via config cycling
before this call. If the tag doesn't match the assigned model, report it but
don't retry — trust the config.
```

---

## Model Tagging Rule

Every stage prompt MUST include this instruction:

```
At the top of your output, write exactly: [MODEL: your-model-name, PROVIDER: your-provider]
This tag is an audit trail. The actual model routing was set via config cycling
before this call. If the tag doesn't match the assigned model, report it but
don't retry — trust the config.
```

This tag is an audit trail. The actual model routing is guaranteed by config cycling,
not by the tag. If the tag is missing or wrong, check config rather than retrying.

## Using Guardrails in Practice

When delegating a stage, the prompt structure is:

```
[FABLE STAGE: StageName]

TASK: [what to do]
WHY THIS MATTERS: [the user's real goal — why this task exists, not just what it produces]
CONTEXT: [prior outputs, file paths, dependencies]

BEHAVIORAL DIRECTIVES:
- Lead with the outcome. [stage-specific wording]
- Ground every claim. If you cannot verify a claim, say "unverified".
- Match effort to the task. [stage-specific effort level]

GUARDRAILS:
[Stage-specific guardrails]

INSTRUCTIONS:
- [Specific instructions]
- Save your complete output to: [file_path]
- Return only a brief status message.
```

The `WHY THIS MATTERS` field is derived from Anthropic's "give the reason, not just the request" principle. When the subagent understands why the task exists, it makes better decisions about what to prioritise, what to cut, and what the reader actually needs. Fill it in from the user's original request — not a restatement of the task, but the outcome they're trying to achieve.

Example for Research:
```
[FABLE STAGE: Research]

TASK: Write a competitive analysis of AI ghostwriting tools.

WHY THIS MATTERS: The user needs to decide which AI ghostwriting tool to recommend to their digital marketing clients — this determines purchasing recommendations, not just rankings.

BEHAVIORAL DIRECTIVES:
|- Lead with the outcome. Your first sentence should answer what you found, not what you're about to do.
|- Ground every claim. If you cannot verify a claim against a source, say "unverified" — do not present it as confirmed.
|- Match effort to the task. This is RESEARCH: gather broadly, move fast, don't over-analyse individual sources.
|- ASYNC: This stage runs in the background via delegate_task(background=true). Write your output file BEFORE reporting completion — the orchestrator will verify it after you finish.

GUARDRAILS:
|- If you cite percentages, rates, or benchmarks, label the exact source and date.
|- Lead with caveats before specific numbers.
|- Do not present vendor claims as verified facts unless independently corroborated.
|- Save your complete output to: ./stage1_research.md
- At the top of your output, write exactly: [MODEL: deepseek-v4-flash, PROVIDER: opencode-go]
This tag is an audit trail. The actual model routing was set via config cycling
before this call. If the tag doesn't match the assigned model, report it but
don't retry — trust the config.

INSTRUCTIONS:
- Gather 5+ competitor landing pages.
- Extract pricing, features, and target audience for each.
- Verify every URL returns HTTP 200.
- Save to ./stage1_research.md.
- Return only a brief status message.
```

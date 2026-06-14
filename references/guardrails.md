# Prompt Guardrails for Fable Orchestrator

These guardrails are injected into every stage prompt by the programmatic
tool (`scripts/fable_orchestrator.py`). They are not suggestions — they are
mandatory instructions appended to each stage's prompt.

## Research Stage

- If you cite percentages, rates, or benchmarks, label the exact source and date.
- Lead with caveats before specific numbers. If data is contested, say so.
- Do not present vendor claims as verified facts unless independently corroborated.
- Note pricing volatility: AI tool prices change frequently; flag promotional vs. stable rates.

## Plan Stage

- Segment the audience into at least 3 tiers (solo/freelance, small agency, in-house team).
- Map every recommendation to a specific tier or use-case.
- Include a "Methodology & Caveats" section in the plan.
- Flag any predetermined conclusions; the plan must remain neutral.

## Implementation Stage

- Write the deliverable as if the reader will make purchasing decisions from it.
- Every claim must trace to a source; unsupported claims must be flagged as unverified.
- If a feature was not hands-on tested, explicitly state "described by vendor, not independently verified."
- The final line must not reveal a predetermined conclusion unless the analysis genuinely arrived there.

## Verification Stage

- Check for internal consistency across all prior stages.
- Flag any hallucination data that shifts between stages or uses different benchmarks.
- Verify URLs are live (HTTP 200) and pricing matches current vendor pages.
- Flag pricing volatility and promotional vs. stable rates.
- List all factual errors with exact corrections.
- Output a "Corrections to apply" section.

## Critique Stage

- Check for confirmation bias: was the conclusion predetermined?
- Verify competitor selection is justified; flag unexplained exclusions.
- Assess whether the audience segmentation is adequate.
- Check if verification errors were propagated back or ignored.
- Identify 3+ concrete weaknesses.
- Output a "Priority fixes" ranked list.

## Consolidation Stage

- Read all prior stage outputs (research, plan, implement, verify, critique).
- Produce a single, canonical final deliverable.
- Apply every correction from the verification stage.
- Address every priority fix from the critique stage.
- Remove any predetermined conclusions unless independently justified.
- Add a "Version & Caveats" header stating: (a) what was desk-researched, (b) what was hands-on tested, (c) pricing recheck date.
- This is the ONLY published version; all prior stages are working drafts.

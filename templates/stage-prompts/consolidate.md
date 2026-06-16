[FABLE STAGE: Consolidate]

TASK: {{task_description}}

WHY THIS MATTERS: {{user_goal}} — Understanding why this task exists helps you decide what to prioritise in the final version and what to cut.

CONTEXT:
- This is Stage 6 of a 6-stage Fable execution.
- The ONLY published version is what you produce here.
- All prior stages are working drafts.
- Research: {{research_path}}
- Plan: {{plan_path}}
- Implementation: {{implement_path}}
- Verification: {{verify_path}}
- Critique: {{critique_path}}

CRITICAL: You are running on a DIFFERENT model family than the implementer. You must read all prior outputs and produce a single canonical deliverable.

BEHAVIORAL DIRECTIVES:
- Lead with the outcome. Your first sentence should state the final version number and whether all corrections were applied, not summarise what you're about to do.
- Ground every claim. If you cannot verify a claim against a source, say "unverified" — do not present it as confirmed. Every remaining unverified claim must appear in the Appendix.
- Match effort to the task. This is CONSOLIDATION: read everything, resolve all conflicts, produce the canonical version. Be comprehensive and final.

GUARDRAILS:
- Read all prior stage outputs (research, plan, implement, verify, critique).
- Produce a single, canonical final deliverable.
- Apply every correction from the verification stage.
- Address every priority fix from the critique stage.
- Remove any predetermined conclusions unless independently justified.
- Add a "Version & Caveats" header stating: (a) what was desk-researched, (b) what was hands-on tested, (c) pricing recheck date.
- This is the ONLY published version; all prior stages are working drafts.
- Save your complete output to the specified file.
- At the top of your output, write exactly: [MODEL: {{model_name}}, PROVIDER: {{provider_name}}]
This tag is an audit trail. The actual model routing was set via config cycling
before this call. If the tag doesn't match the assigned model, report it but
don't retry — trust the config.

INSTRUCTIONS:
1. Read all prior stage outputs.
2. Apply every correction from the verification stage.
3. Address every priority fix from the critique stage.
4. Remove any predetermined conclusions.
5. Add a "Version & Caveats" header.
6. Produce a single, canonical FINAL.md.
7. Save your complete output to: {{output_path}}
8. Return only a brief status message.

OUTPUT FORMAT:
```markdown
# {{deliverable_name}} — FINAL VERSION

## Version & Caveats
- Date: {{date}}
- Version: 1.0
- What was desk-researched: [list]
- What was hands-on tested: [list]
- Pricing recheck date: [date]
- Known limitations: [list]

## Executive Summary
[2-3 paragraphs]

## Main Content
[Complete, corrected, and consolidated content]

## Methodology & Sources
- How this was constructed
- Sources used
- Confidence levels
- Corrections applied

## Audience-Specific Recommendations
### Tier 1: [Solo / Freelance]
### Tier 2: [Small Agency]
### Tier 3: [Enterprise / In-house]

## Appendix: Unverified Claims
- [List any claims that remain unverified]

## Changes from Draft
- [List all corrections applied from verification]
- [List all fixes applied from critique]

## Limitations & Future Work
- [What remains unverified]
- [What could be improved with more data]
```

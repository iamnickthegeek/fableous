[FABLE STAGE: Consolidation]

TASK: {{task_description}}

CONTEXT:
You are the final stage of a 6-stage Fable execution. All prior stages are working drafts. You produce the ONLY published version.

STAGE OUTPUTS:
- Research: {{research_path}}
- Plan: {{plan_path}}
- Implementation: {{implement_path}}
- Verification: {{verify_path}}
- Critique: {{critique_path}}

INSTRUCTIONS:
1. Read all prior stage outputs.
2. Apply every correction from the verification stage.
3. Address every priority fix from the critique stage.
4. Remove any predetermined conclusions.
5. Add a "Version & Caveats" header.
6. Produce a single, canonical FINAL.md.
7. Save to: {{output_path}}
8. Return only a brief status message.

GUARDRAILS:
- Read all prior stage outputs.
- Produce a single, canonical final deliverable.
- Apply every correction from the verification stage.
- Address every priority fix from the critique stage.
- Remove any predetermined conclusions unless independently justified.
- Add a "Version & Caveats" header.
- This is the ONLY published version.
- Save your complete output to: {{output_path}}
- At the top of your output, write exactly: [MODEL: {{model_name}}, PROVIDER: {{provider_name}}]
This tag is an audit trail. The actual model routing was set via config cycling
before this call. If the tag doesn't match the assigned model, report it but
don't retry — trust the config.

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

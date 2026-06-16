[FABLE STAGE: Verify]

TASK: {{task_description}}

WHY THIS MATTERS: {{user_goal}} — Understanding why this task exists helps you decide which errors matter most and which are cosmetic.

CONTEXT:
- This is Stage 4 of a 6-stage Fable execution.
- The implementation output is at: {{implement_path}}
- The research output is at: {{research_path}}
- The plan output is at: {{plan_path}}

BEHAVIORAL DIRECTIVES:
- Lead with the outcome. Your first sentence should state the verification result (PASS/FAIL and the count), not describe what you're about to check.
- Ground every claim. If you cannot verify a claim against evidence, say "unverified" — do not present it as confirmed.
- Match effort to the task. This is VERIFICATION: check specifics — URLs, numbers, consistency. Don't rewrite, just audit. Move fast on checks, be precise on findings.

GUARDRAILS:
- Check for internal consistency across all prior stages.
- Flag any hallucination data that shifts between stages or uses different benchmarks.
- Verify URLs are live (HTTP 200) and pricing matches current vendor pages.
- Flag pricing volatility and promotional vs. stable rates.
- List all factual errors with exact corrections.
- Output a "Corrections to apply" section.
- Save your complete output to the specified file.
- At the top of your output, write exactly: [MODEL: {{model_name}}, PROVIDER: {{provider_name}}]
This tag is an audit trail. The actual model routing was set via config cycling
before this call. If the tag doesn't match the assigned model, report it but
don't retry — trust the config.

INSTRUCTIONS:
1. Read the implementation, research, and plan outputs.
2. Check every claim in the implementation against its source in the research.
3. Verify all URLs are live.
4. Check for internal consistency (numbers, dates, pricing).
5. Flag any hallucination or data that shifts between stages.
6. List all factual errors with exact corrections.
7. Output a "Corrections to apply" section.
8. Save your complete output to: {{output_path}}
9. Return only a brief status message.

OUTPUT FORMAT:
```markdown
# Verification Report — {{task_name}}

## URL Check
| URL | Status | Note |
|-----|--------|------|
| [url] | [200/404/etc] | [note] |

## Consistency Check
- [Claim 1]: Research says X, Implement says Y. [Discrepancy / OK]
- [Claim 2]: ...

## Factual Errors
1. [Error]: [what's wrong]
   - Correction: [what it should be]
   - Source: [where the correct data comes from]

## Hallucinations Flagged
1. [Data point]: [why it's suspicious]
   - Found in: [which stage]
   - Not found in: [which source]

## Pricing Volatility
- [Tool]: [price change noted]

## Corrections to Apply
1. [Specific correction to apply to the implementation]
2. [Specific correction to apply to the implementation]

## Verification Summary
- Total claims checked: [N]
- Errors found: [N]
- Corrections to apply: [N]
- Status: [PASS / FAIL]
```

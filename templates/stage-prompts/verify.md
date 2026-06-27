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
6. CROSS-RUN RECONCILIATION (v0.8.0): Use search_files to look for prior run outputs (FINAL.md, stage*.md) in the project directory. If prior outputs exist, read them and compare key stats against the current implementation. Flag any discrepancies (same metric at different values, contradictory trends). Log in a "Cross-Run Discrepancies" section.
7. METHODOLOGY CONSISTENCY (v0.8.0): For research-type tasks, pick 3 key stats that appear across multiple sources. Verify they use the same measurement methodology (e.g., engagement rate definition, sample size, time window). Flag stats where sources may measure different things but present them as comparable.
8. List all factual errors with exact corrections.
9. Output a "Corrections to apply" section.
10. Save your complete output to: {{output_path}}
11. Return only a brief status message.

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

## Cross-Run Discrepancies (v0.8.0)
[If prior run outputs were found in the project directory, list any stat discrepancies between runs. If no prior outputs exist, write "No prior run outputs found in project directory."]
- [Metric]: Current run says [X], prior run says [Y]. [Likely cause: different source / different methodology / data drift]
- [Metric]: ...

## Methodology Consistency (v0.8.0)
[For research-type tasks. If not a research task, write "Not applicable — non-research deliverable."]
- [Stat 1]: Sources [A] and [B] both cite this metric. [Same / different] methodology. [Note any definitional differences.]
- [Stat 2]: ...
- [Stat 3]: ...

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

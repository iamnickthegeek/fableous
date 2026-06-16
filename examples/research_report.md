# Example: Research Report

## Task

"Write a 1-page competitive analysis of AI ghostwriting tools for digital marketers, with 3 real competitors, verified pricing, and cited sources."

## Execution

### Step 1: Create the stage map

```
todo(todos=[
  {id: "stage-1", content: "Stage 1: Research — gather 5+ competitor pages, extract pricing, verify URLs", status: "pending"},
  {id: "stage-2", content: "Stage 2: Plan — structure, audience tiers, methodology", status: "pending"},
  {id: "stage-3", content: "Stage 3: Implement — write first draft with all sources", status: "pending"},
  {id: "stage-4", content: "Stage 4: Verify — check URLs, trace claims, check consistency", status: "pending"},
  {id: "stage-5", content: "Stage 5: Critique — independent review, name weaknesses", status: "pending"},
  {id: "stage-6", content: "Stage 6: Consolidate — canonical FINAL.md with all fixes", status: "pending"},
])
```

### Step 2: Execute Stage 1 (Research)

Delegate to `deepseek-v4-flash` via Opencode Go.

Prompt:
```
[FABLE STAGE: Research]

Task: Write a competitive analysis of AI ghostwriting tools for digital marketers.

GUARDRAILS:
- If you cite percentages, label the exact source and date.
- Lead with caveats.
- Do not present vendor claims as verified facts.
- Save your complete output to: ./stage1_research.md
- At the top of your output, write exactly: [MODEL: deepseek-v4-flash, PROVIDER: opencode-go]

INSTRUCTIONS:
- Gather 5+ competitor landing pages (Jasper.ai, Copy.ai, Writesonic, etc.).
- Extract pricing, features, and target audience for each.
- Verify every URL returns HTTP 200.
- Save to ./stage1_research.md.
```

After completion:
- Read stage1_research.md
- Verify first line: [MODEL: deepseek-v4-flash, PROVIDER: opencode-go]
- Verify URLs with terminal(curl):
  ```
  terminal(command="curl -s -o /dev/null -w '%{http_code}' https://jasper.ai")
  # Must return "200"
  ```
- Verify output contains "Source:" for every claim
- Update todo
- Update WORK_LOG.md

### Step 3: Execute Stage 2 (Plan)

Delegate to `glm-5.1` via Opencode Go.

Run in parallel with Stage 1 if both are pending.

After completion:
- Verify model tag
- Verify output contains "Methodology & Caveats"
- Verify audience segmented into 3 tiers:
  - Solo/freelance
  - Small agency
  - In-house team
- Update todo
- Update WORK_LOG.md

### Step 4: Execute Stage 3 (Implement)

Delegate to `kimi-k2.6` via Opencode Go.

Depends on Stage 1 and Stage 2.

After completion:
- Verify model tag
- Verify output traces every claim to a source
- Verify word count: 800-1200 words
- Verify structure: Executive Summary, Comparison Table, Recommendations
- Update todo
- Update WORK_LOG.md

### Step 5: Execute Stage 4 (Verify)

**Verification checks (mandatory):**

1. URL verification:
```
# For each URL in stage1_research.md:
terminal(command="curl -s -o /dev/null -w '%{http_code}' URL", timeout=30)
# Must return "200"
```

2. Source tracing:
```
read_file(path="./stage3_implement.md")
# Every claim must have a source citation
# Check that each claim maps back to stage1_research.md
```

3. Consistency check:
```
read_file(path="./stage3_implement.md")
# Check that pricing data is consistent with stage1_research.md
# Check that feature lists don't contradict
```

4. Hallucination check:
```
read_file(path="./stage3_implement.md")
# Flag any data that doesn't appear in stage1_research.md
```

If ANY check fails, the stage is NOT complete.

Delegate to `deepseek-v4-pro` via Opencode Go.

**Critical:** Must be a different model family than Implement (DeepSeek vs Kimi).

After completion:
- Run verification checks
- Verify model tag
- Update todo
- Update WORK_LOG.md

### Step 6: Execute Stage 5 (Critique)

Delegate to `glm-5.1` via Opencode Go.

**Critical:** Must be a different model family than Implement (GLM vs Kimi).

Prompt:
```
[FABLE STAGE: Critique]

Task: Write a competitive analysis of AI ghostwriting tools for digital marketers.

Context:
- Implementation: [from stage3_implement.md]
- Verification: [from stage4_verify.md]

GUARDRAILS:
- Check for confirmation bias.
- Verify competitor selection is justified.
- Assess audience segmentation.
- Check if verification errors were propagated.
- Identify 3+ concrete weaknesses.
- Save your complete output to: ./stage5_critique.md
- At the top of your output, write exactly: [MODEL: glm-5.1, PROVIDER: opencode-go]

INSTRUCTIONS:
- Review the competitive analysis.
- Check if the conclusion was predetermined.
- Verify all 3 competitors are justified.
- Check if any competitors were excluded without explanation.
- Assess if the audience segmentation is adequate.
- Check if verification errors were fixed or ignored.
- Identify 3+ concrete weaknesses.
- Save to ./stage5_critique.md.
```

### Step 7: Execute Stage 6 (Consolidate)

Delegate to `deepseek-v4-pro` via Opencode Go.

Read all prior stage outputs. Apply corrections. Produce FINAL.md.

After completion:
- Verify model tag
- Verify FINAL.md exists
- Verify "Version & Caveats" header present:
  - Date
  - What was desk-researched
  - What was hands-on tested
  - Pricing recheck date
- Verify all verification corrections applied
- Verify all critique fixes addressed or flagged
- Update todo
- Update WORK_LOG.md
- Mark task complete

## Expected Output

```
.
├── stage1_research.md
├── stage2_plan.md
├── stage3_implement.md
├── stage4_verify.md
├── stage5_critique.md
├── FINAL.md
└── WORK_LOG.md
```

## Time Estimate

- Stages 1-2: 15 minutes (can run in parallel)
- Stage 3: 20 minutes
- Stage 4: 15 minutes (includes URL verification)
- Stage 5: 15 minutes
- Stage 6: 15 minutes
- Total: 60-80 minutes

## Verification Gates

- [ ] All 5+ URLs return HTTP 200
- [ ] Every claim traces to a source
- [ ] No hallucinations (data not in research)
- [ ] Pricing is consistent across stages
- [ ] All model verifications pass
- [ ] Cross-family verification: Verify ≠ Implement, Critique ≠ Implement
- [ ] FINAL.md contains "Version & Caveats" header
- [ ] All verification corrections applied
- [ ] All critique fixes addressed or flagged

# Example: Simple Task

## Task

"Write a blog post about the benefits of AI ghostwriting for digital marketers."

## Execution

### Step 1: Create the stage map

```
todo(todos=[
  {id: "stage-1", content: "Stage 1: Research — gather 3+ sources on AI ghostwriting", status: "pending"},
  {id: "stage-2", content: "Stage 2: Plan — outline, audience, tone", status: "pending"},
  {id: "stage-3", content: "Stage 3: Implement — write the blog post", status: "pending"},
  {id: "stage-4", content: "Stage 4: Verify — check facts, plagiarism, tone", status: "pending"},
  {id: "stage-5", content: "Stage 5: Critique — independent review", status: "pending"},
  {id: "stage-6", content: "Stage 6: Consolidate — canonical FINAL.md", status: "pending"},
])
```

### Step 2: Execute Stage 1 (Research)

Delegate to `deepseek-v0.4.0-flash` via Opencode Go.

Prompt:
```
[FABLE STAGE: Research]

Task: Write a blog post about AI ghostwriting for digital marketers.

GUARDRAILS:
- If you cite percentages, label the exact source and date.
- Lead with caveats.
- Do not present vendor claims as verified facts.
- Save your complete output to: ./stage1_research.md
- At the top of your output, write exactly: [MODEL: deepseek-v0.4.0-flash, PROVIDER: opencode-go]

INSTRUCTIONS:
- Gather 3+ sources on AI ghostwriting for digital marketers.
- Extract key statistics, benefits, and case studies.
- Verify URLs are live.
- Save to ./stage1_research.md.
```

After completion:
- Read stage1_research.md
- Verify first line: [MODEL: deepseek-v0.4.0-flash, PROVIDER: opencode-go]
- Verify URLs with web_search or terminal(curl)
- Update todo
- Update WORK_LOG.md

### Step 3: Execute Stage 2 (Plan)

Delegate to `glm-5.1` via Opencode Go.

Run in parallel with Stage 1 if both are pending.

After completion:
- Verify model tag
- Verify output contains "Methodology & Caveats"
- Verify audience segmentation into 3+ tiers
- Update todo
- Update WORK_LOG.md

### Step 4: Execute Stage 3 (Implement)

Delegate to `kimi-k2.6` via Opencode Go.

Depends on Stage 1 and Stage 2.

After completion:
- Verify model tag
- Verify output traces every claim to a source
- Verify word count (800-1200 words)
- Verify tone matches audience
- Update todo
- Update WORK_LOG.md

### Step 5: Execute Stage 4 (Verify)

Delegate to `deepseek-v0.4.0-pro` via Opencode Go.

After completion:
- Verify model tag (different from Implement)
- Verify URLs are live
- Verify internal consistency
- List factual errors with corrections
- Update todo
- Update WORK_LOG.md

### Step 6: Execute Stage 5 (Critique)

Delegate to `glm-5.1` via Opencode Go.

**Critical:** Must be a different model family than Implement (GLM vs Kimi).

After completion:
- Verify model tag
- Verify 3+ concrete weaknesses identified
- Verify confirmation bias checked
- Update todo
- Update WORK_LOG.md

### Step 7: Execute Stage 6 (Consolidate)

Delegate to `deepseek-v0.4.0-pro` via Opencode Go.

Read all prior stage outputs. Apply corrections. Produce FINAL.md.

After completion:
- Verify model tag
- Verify FINAL.md exists
- Verify "Version & Caveats" header present
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

- Stages 1-2: 10 minutes (can run in parallel)
- Stage 3: 15 minutes
- Stage 4: 10 minutes
- Stage 5: 10 minutes
- Stage 6: 10 minutes
- Total: 45-55 minutes

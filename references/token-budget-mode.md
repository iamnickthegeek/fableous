# Token-Budget / Lightweight Mode — Worked Example

This reference documents the token-budget test pattern demonstrated in a June 2026 Fable execution. It proves that Fable's pipeline structure catches real errors even when all stages run on a single cheap model.

## The Task

Write a brief competitive comparison of three AI writing assistants (Jasper, Copy.ai, Writesonic) including pricing, free tier availability, and one distinguishing feature per tool. Verify claims against actual websites. Target: solo content creator on a tight budget. Under 400 words.

Explicit constraints: "Use the cheapest models in the routing table for each stage. Keep every stage output brief — this is a token-budget test, not a full production run."

## Execution Parameters

| Parameter | Value |
|-----------|-------|
| Model (all stages) | `deepseek-v0.4.0-flash` (Opencode Go) |
| Config cycling | `route_config.py set --model deepseek-v0.4.0-flash --provider opencode-go` before each stage |
| Mode | Sync (all stages sequential — no async overhead on a small task) |
| Output dir | `/tmp/fable-test-7-1/` |
| Stages | All 6: Research → Plan → Implement → Verify → Critique → Consolidate |

## What Fable Caught

The Verify stage (Stage 4) identified **2 factual errors** in the Implement draft:

1. **Writesonic pricing**: Draft said $16/mo Lite. Live sources confirmed the plan is now ~$39/mo (2026 pricing). Outdated by $23.
2. **Writesonic free tier**: Draft said "25 credits/month free ongoing." Live sources confirmed 25 one-time credits — effectively a trial, not a sustainable free plan.

Both errors favoured Writesonic in the comparison. Once corrected, the recommendation flipped:
- Before correction: "Writesonic wins on affordability" ✅
- After correction: "Copy.ai's free 2,000 words/mo is the best entry point; Writesonic ties Jasper at ~$39/mo with weaker features" ❌

The Critique stage (Stage 5) independently flagged confirmation bias in the draft — the two wrong claims were precisely what propped up the Writesonic recommendation.

## What This Proves

Token-budget mode (single cheap model, all stages) still provides real value:

- **The pipeline structure catches errors even on weak models.** The verification subagent found the pricing discrepancies by checking live URLs. The critique subagent identified confirmation bias. Neither needed a stronger model — they just needed the structured pipeline.
- **Config cycling works reliably with explicit model overrides.** `route_config.py set --model deepseek-v0.4.0-flash --provider opencode-go` set the model correctly for every stage. The subagent summary incorrectly reported `deepseek-v0.4.0-pro` (Pitfall 10), but output file model tags and `route_config.py verify` confirmed `deepseek-v0.4.0-flash` every time.
- **Token-budget mode is better than skipping Fable entirely.** A one-shot attempt would have published the wrong pricing and free-tier details. The pipeline caught both before consolidation.

## Output Files

```
/tmp/fable-test-7-1/
├── FINAL.md              # Canonical output (330 words, comparison table, sources)
├── WORK_LOG.md           # Session log
├── stage1_research.md    # Raw research (ground truth sources)
├── stage2_plan.md        # Outline (structure and word allocation)
├── stage3_implement.md   # First draft (contained the 2 errors)
├── stage4_verify.md      # Verification report (found the 2 errors)
└── stage5_critique.md    # Critique (flagged confirmation bias)
```

## When to Use vs When Not To

**Use token-budget mode when:**
- User explicitly says "cheapest models", "token-budget test", "keep brief"
- The deliverable is under 500 words or 1 page
- The cost of being slightly wrong (nuance, tone) is lower than the cost of being wrong about factual claims
- You have rate-limit or budget constraints with premium models

**Don't use token-budget mode when:**
- Cross-family verification is critical (e.g., code correctness, financial analysis, legal review)
- The user expects production-quality output with no tradeoffs
- The task requires deep reasoning or subtle judgment calls
- You haven't been told to economise — the default routing table is the default for a reason

## Quality Tradeoffs Beyond Cost (v0.8.0)

The single-model vs. multi-model choice is not only about cost. Analysis of three deliverables produced from the same prompt (one single-pass, one single-model staged, one multi-model staged) revealed distinct quality character differences:

**Single-model flatlining produces:**
- **Voice consistency** — the same model's tone carries through all stages. No "written by committee" feel.
- **Deeper self-critique** — the same model applying its critical lens across multiple passes develops coherent internal critique. It knows its own blind spots better than a different model that lacks context.
- **Consistent data interpretation** — one model reads sources the same way throughout, reducing the risk of interpretive drift between stages.
- **Risk: Cognitive monoculture** — the model's blind spots propagate through every stage. If the model has a systematic bias (e.g., over-trusting vendor sources), no stage breaks it.

**Multi-model routing produces:**
- **Creative range** — different model families excel at different things. One model may produce better structured templates, another better strategic framing, another sharper critique. The deliverable benefits from this range.
- **Cross-family error catching** — a weakness one model can't see in its own output may be obvious to a different architecture.
- **Risk: Voice inconsistency** — the document may feel like it was written by different people. Tone shifts between sections. Data discrepancies can emerge when different research passes find different sources.
- **Risk: Over-hedging** — when a different model family critiques the implementation, it may apply fixes that don't suit the deliverable type (e.g., adding legal-grade caveats to a punchy research brief). The v0.8.0 fix calibration addresses this.

**Decision guidance by deliverable type:**
| Deliverable Type | Recommended Mode | Why |
|---|---|---|
| Research Brief | Single-model | Voice consistency matters most |
| Execution Playbook | Multi-model | Creative range produces better templates and scripts |
| Credential Asset | Multi-model | Cross-family verification strengthens defensibility |
| Reference Document | Either | Both work; choose based on cost |
| Decision Memo | Multi-model | Multiple perspectives improve the analysis |

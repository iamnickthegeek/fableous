# Pricing Verification Volatility — Live Pattern (June 2026)

**What this documents:** Two consecutive Fable executions, 90 minutes apart, verified the same SaaS pricing claim (Writesonic) and got different "current" prices. This is not a bug — it's the nature of fast-moving SaaS pricing data. The pattern is: (1) research finds a stale number, (2) verify catches it, (3) but multiple verify runs may find different "current" numbers because sources update at different speeds.

## The Pattern (Two Consecutive Tests)

### Test 7-1 (token-budget, single-model)

| Stage | What claimed | What verified | Gap |
|-------|-------------|---------------|-----|
| Research | Writesonic $16/mo Lite | — | — |
| Implement | Writesonic $16/mo Lite | — | — |
| Verify | — | ~$39/mo Lite (2026 update) | +$23 |
| Result | Recommendation flipped: Writesonic no longer budget winner | | |

### Test 7-2 (full pipeline, multi-model, ~90 min later)

| Stage | What claimed | What verified | Gap |
|-------|-------------|---------------|-----|
| Research | Writesonic $16/mo Individual | — | — |
| Implement | Writesonic $16-20/mo Individual | — | — |
| Verify | — | $79/mo Starter (April 2026 restructure) | +$63 |
| Result | Recommendation flipped: Copy.ai wins, Writesonic is most expensive | | |

### The Two Verifies Disagreed With Each Other

Both Verify stages checked the same claim against live sources. Both correctly caught the $16/mo as outdated. But they returned different corrections:

| Verify Stage | Reported "Current" Price | Source Window |
|-------------|--------------------------|---------------|
| Test 7-1 (deepseek-v0.4.0-flash) | ~$39/mo Lite | Caught the mid-cycle price bump |
| Test 7-2 (deepseek-v0.4.0-pro) | $79/mo Starter | Caught the April 2026 full restructure |

Both were "correct" for their search window — the $39/mo figure was still indexed in some sources, while the $79/mo reflected the post-restructure reality. This is NOT a failure of either verification stage. It's the nature of pricing data decay.

## Why This Happens

1. **SaaS pricing pages change without version history.** There's no changelog for most pricing updates. Old prices persist in review articles, comparison sites, and forum posts for months.
2. **Web search indexes multiple time horizons.** A single `web_search` may return a mix of articles from last week and last year, all claiming to show "current" pricing.
3. **Restructures (not just price changes) are hardest to catch.** A $16→$39 bump is a price update. A $16→$79 jump with renamed plans (Individual → Starter) is a restructure — the old URLs, plan names, and feature sets all change. Search engines take weeks to fully re-index.
4. **Price change vs. plan restructure.** Both tests caught a wrong number, but test 7-2 caught a deeper structural change (the entire Individual tier was killed and replaced). This is harder to detect because you need to notice the absence of the old plan name in search results, not just a different number next to the same plan.

## Verification Protocol for Fast-Moving Pricing

Based on this pattern, the Verify stage should apply these techniques for ANY pricing claim:

1. **Cross-reference multiple sources.** Don't stop at one search result. Check the official pricing page PLUS 2-3 independent review sites. If they disagree, flag it.
2. **Check for plan-name changes.** If the plan name in the draft (e.g., "Individual") doesn't appear in current search results for the official site, the entire pricing structure may have changed — not just the number.
3. **Look for "restructured" or "pivot" signals.** When a vendor announces a product pivot (as Writesonic did with "AI Search Growth Engine"), pricing often changes simultaneously. The research stage should note pivots; the verify stage should double-check pricing when a pivot is mentioned.
4. **Note the verification date prominently.** FINAL.md should include a publication date and verification note so readers know when the pricing was checked. This is already required (Version & Caveats header), but it's especially important for pricing claims.
5. **Consider pricing source freshness.** A review article from January 2026 reporting "current" pricing may be 5 months stale by June. Prefer sources dated within 30 days for pricing claims.

## What This Proves About Fable

The pipeline caught the wrong pricing in BOTH tests despite using different models and different execution modes:

- Test 7-1: Single cheap model (deepseek-v0.4.0-flash), still caught the error
- Test 7-2: Multi-model routing, caught a deeper restructure

The structure (separate Research → Verify → Critique → Consolidate stages) is what catches errors, not model quality. Even with a weak model, a separate Verify stage asking "are these claims actually true RIGHT NOW?" catches things a single-pass draft never would.

# Case Study: Building the Ronin Partner Finder Skill with Fable v6

## Context

Built a Hermes-native skill that finds and scores two flavors of partnership targets from public web sources:

- **Ronin buyer/investor** — owners of newsletters, YouTube channels, podcasts, blogs, Skool/FB groups, or email lists who already monetise via sponsorships/ads but are under-monetising.
- **Beamer profit-center investor** — established coaches/consultants/experts with a proven $10k+ offer and a customer database, where the operator funds lead gen + sales.

Source training material: Royalty Ronin and Beamer Method transcripts and PDFs in `/home/case/.hermes/projects/royalty-ronin/`.

## Ideal partner profile

### Universal must-haves
- Established business, not a startup.
- Existing buying audience or customer database (5k+ emails / 10k+ followers / past buyers).
- Already monetising (products, sponsorships, ads, affiliates, paid traffic).
- Willing to revenue-share.
- Niche alignment: health, wealth, love/relationships, e-commerce, home services, finance, real estate.
- Willing to give access to lists/assets.

### Ronin-specific
- Owns a distribution asset.
- Already monetises via sponsorships, ads, shout-outs, affiliates, or communities.
- Has under-monetised assets (dormant lists, old content, neglected traffic).

### Beamer-specific
- Proven high-ticket offer ($10k+) with capacity for 50+ new clients.
- Track record of sales and client satisfaction.
- Emotional intelligence / abundance mindset; not a control freak about lists.

### Disqualifiers
- No audience, no buyers, no product.
- Scarcity/control-freak mindset about lists.
- Bad reputation.
- Wants you to build brand/product/traffic from scratch.
- Flaky, unreachable, or excessive gatekeepers.

## Scoring rubric (0–100)

| Criterion | Weight | Public-web signals |
|-----------|--------|--------------------|
| Audience / asset base | 25 | Subscriber/member counts, customer claims, about-page stats |
| Monetisation proof | 20 | Pricing, sponsor/advertise page, affiliate program, paid-ad footprint, events |
| Offer / deal fit | 20 | Distribution asset OR high-ticket offer + client capacity |
| Business maturity | 15 | Founded date, team page, premium cart/CRM, press/book |
| Niche alignment | 10 | Bio, categories, content topics |
| Partnerability | 10 | Abundance language, open contact, sponsor inquiries welcomed |

Score bands: 90–100 dream, 75–89 strong, 50–74 test, <50 disqualified.

## Lead sources and example queries

- **Newsletters:** `site:substack.com {{niche}} newsletter sponsor`, `site:paved.com {{niche}} newsletter`
- **YouTube:** `"{{niche}}" YouTube channel sponsor contact`, `videos.feedspot.com {{niche}}_youtube_channels`
- **Podcasts:** `"{{niche}}" podcast "advertise" OR "sponsor"`, `site:listennotes.com {{niche}} podcast`
- **Skool / FB groups:** `site:skool.com {{niche}} community`, `site:facebook.com/groups {{niche}} coaching`
- **Blogs:** `"{{niche}}" blog "advertise with us"`, `site:paved.com {{niche}}`
- **Course directories:** `best {{niche}} coaching program 2024`, `"{{niche}}" mastermind "$10,000"`

## Outreach stances

- **Ronin:** "I'm looking to BUY sponsorships/ad space/partnerships in {{niche}}." Buyer/investor posture, not vendor.
- **Beamer:** "I've got capital to invest in established {{niche}} businesses. I'll fund your phoneless lead gen and sales team for your high-ticket offer." Investor posture.

## Fable v6 lesson: model-mismatch recovery

During Stage 4 (Verify), the subagent output began with `[MODEL: deepseek-v4-pro, PROVIDER: opencode-go]` but the `delegate_task` metadata reported `model: kimi-k2.7-code`. Because Verify must be cross-family from Implement (Kimi), the verification was re-run via:

```bash
hermes chat -q 'STAGE_PROMPT' -m deepseek-v4-pro --provider opencode-go -Q -t file
```

This confirmed the pass. Always trust the tool metadata over the tag when they disagree.

## Fable v6 lesson: timeout recovery

During Stage 4 (Verify) and Stage 5 (Critique) for the author variant, `delegate_task` timed out after 600s. In both cases the deliverable file had already been written to disk. Rather than re-running the whole stage, the output was read directly and re-verified via the terminal method. See `references/timeout-recovery-recipe.md`.

## Author variant

A second skill variant was built for health & wellness authors (including mental health). The pitch is a mini-course revenue-share: the operator turns the author's existing book into a short course and sells it to the author's list.

- Skill: `/home/case/.hermes/projects/royalty-ronin/stage3_skill/author-partner-finder/`
- Verification: `/home/case/.hermes/projects/royalty-ronin/stage4_verification_authors.md`
- Critique fixes: `/home/case/.hermes/projects/royalty-ronin/stage5_fixes.md`

## Critique-driven fixes

Stage 5 critique surfaced issues in scoring, compliance, and sources. Fixes applied before consolidation:
- Operator identity guard and default placeholder name.
- Strict must-have gate (missing must-haves force `disqualified`).
- Evidence-quality flags and snippet-only score cap.
- Compliance footer in outreach templates.
- Parameterized year tokens and excluded aggregator URL patterns.
- Beamer-specific query sources.
- `TERMS.md` with IP/licensing and platform-compliance warnings.

## Artifacts

- Research: `/home/case/.hermes/projects/royalty-ronin/stage1_research.md`
- Plan: `/home/case/.hermes/projects/royalty-ronin/stage2_plan.md`
- Skill files: `/home/case/.hermes/projects/royalty-ronin/stage3_skill/ronin-partner-finder/`
- Verification: `/home/case/.hermes/projects/royalty-ronin/stage4_verification.md`
- Author skill: `/home/case/.hermes/projects/royalty-ronin/stage3_skill/author-partner-finder/`
- Author verification: `/home/case/.hermes/projects/royalty-ronin/stage4_verification_authors.md`
- Critique: `/home/case/.hermes/projects/royalty-ronin/stage5_critique.md`
- Fixes: `/home/case/.hermes/projects/royalty-ronin/stage5_fixes.md`

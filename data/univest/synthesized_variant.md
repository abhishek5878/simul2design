# V5 — Synthesized variant for Univest ₹1 trial activation (v2 — corrected re-extraction)

> **Generated:** 2026-04-24. **Mode:** balanced. **Confidence:** medium-high.
> Predicted weighted-overall: **44% – 51% – 56%** vs V4 actual **44%** (low to high tier; +0 to +12pt; **median +7pt**).
> **Supersedes** the 2026-04-23 synthesis derived from source-prose-only matrix.

This is the *synthesis*, not the *spec*. The corrected extraction (matrix v2, screenshot-validated) shifts the V5 story materially: most elements we thought we were "introducing" were already present in V4, just unnoticed. v2 V5 stacks **only 1 fully-untested element** (down from 3 in v1).

## The V5 element set (v2)

| Dimension | V4 actual | **V5** | Evidence | Untested? |
|---|---|---|---|---|
| `layout` | `full_screen_dark` | **`full_screen_dark`** | V4 already uses dark theme (corrected from v1). Trust Seeker recovery V3 40% → V4 50% likely from dark-theme-restoration. | — |
| `modal_interrupt` | no | **no** | friction: 31/50 cross-segment in Control. Resolved V1-V4. | — |
| `branding` | `crown_header` | **`crown_header`** | V4 already has crown (corrected from v1). V2/V3/V4 all do. | — |
| `price_visibility` | `visible_with_framing` | **`visible_with_framing`** | All V1-V4 use this banner format (corrected from v1). | — |
| `cta_primary_label` (outline) | "Unlock FREE trade" | **"See 3 real trades, free"** | Matches the actual offer count (banner says "Claim 3 FREE Trades"). Resolves the dual-CTA mismatch friction (33% noticed in V4). | **untested copy** |
| `cta_secondary_label` (sticky) | "Start FREE Trial @ ₹1" | **"Activate for ₹1"** | Cleaner — outline carries the "free" message; sticky carries the activation commitment. | — |
| `cta_style` | outline + sticky green | **outline + sticky green** | V4's high-contrast green sticky on dark theme — preserved at full strength. | — |
| `cta_stack` | `dual_outline_plus_sticky` | **`dual_outline_plus_sticky`** | **User decision (Option B, 2026-04-24)**: preserve V4's dual structure to keep self-segmentation lift; fix the friction via copy coherence, not by removing. | — |
| `urgency_mechanism` | `countdown_timer` | **none** | friction: 6/50 = 41% Skeptical flagged "04:34 Left" as manipulation (corrected — present V1-V4, not V1-only). V5 is first to remove. | (removal — not untested introduction) |
| `refund_or_guarantee_copy` | `implicit_refund` ("Activate @ ₹1 & Get instant refund") | **`explicit_sla`** ("Refund in 60s to source. No questions.") | 64% cite refund as strongest reassurance. Concretization of V4's existing element (corrected from v1). | concretization (not new) |
| `trust_signal` | `regulatory_plus_evidence` (sebi) | **`regulatory_plus_evidence`** (sebi) | V4 already has SEBI (corrected from v1's "implicit"). Universal V1-V4. | — |
| `evidence_detail` | `aggregate_metric` (85%+, 3500+) | **`aggregate_plus_named`** | Restore V1's named-wins carousel (TMPV, ZOMATO, RELIANCE) to coexist with V4's aggregates. 71% of V1 users cited a stock by name. | observed in V1 |
| `trade_evidence` (overlay) | `blurred_card` | **`real_closed_trade`** (entry/exit/days/₹ disclosed) | friction: 12/12 (100% Skeptical) persistent V2-V4. Quote: *"Show me a real trade or don't."* | **untested** |
| `wins_losses_disclosure` (NEW dimension in v2) | no | **yes** ("914 wins · 62 losses" alongside 84.7% accuracy) | V1 prominently displays this. Closes cherry-picking adversary objection structurally. | observed in V1 |
| `trial_offer_count` | 3 | **3** | All variants offer 3 free trades. v1 wrongly assumed 1. Corrected. | — |

## V5 changes vs V4 (the actual diff, corrected)

**7 dimensions change from V4 → V5. Of those:**
- **1 is fully untested**: `trade_evidence=real_closed_trade` (no observed datapoint for the exact UI; mechanism is strong)
- **4 are concretizations or copy fixes**: explicit_sla refines V4's vague "instant refund"; CTA copy makes the offer count consistent; secondary label cleaned; aggregate+named restores V1's pattern V4 dropped
- **2 are observed-pattern adoptions from V1**: `evidence_detail=aggregate_plus_named` and `wins_losses_disclosure=yes` are both V1's strongest trust elements that V2-V4 dropped

The rest of V5 is *V4 preserved correctly* — dark theme, crown, price banner, dual CTA structure, SEBI badge, aggregate metrics, refund banner. Our v1 V5 was over-claiming "new elements" because the v1 matrix mis-extracted V4.

## Per-segment predictions (v2)

| Segment | V4 baseline | V5 low | V5 point | V5 high | Primary drivers (audience reasoning) |
|---|---|---|---|---|---|
| **Skeptical Investor** (24%) | 25% | **30%** | **35%** | **40%** | Real closed trade card removes 100% of segment's persistent friction. Wins/losses disclosure (914W·62L) defeats cherry-picking concern structurally. Explicit SLA concretizes the refund commitment (64% cite as strongest reassurance). Countdown removed (41% flagged as manipulation). Coupling discount 0.7× applied (5 mechanisms target same segment via shared honesty-substrate). |
| **Curious Beginner** (30%) | 33% | **36%** | **41%** | **46%** | V1's named-stock carousel (TMPV, ZOMATO +₹23,435, RELIANCE) restored. The *"I bought it last year — if they nailed that, I should listen"* anchor mechanism. 71% of V1 users cited a stock by name; V2-V4 stripped this and lost the segment. |
| **Bargain Hunter** (26%) | 69% | **63%** | **69%** | **74%** | V4's strongest elements preserved at full strength: green CTA (+16pt observed for this segment), dual-CTA self-segmentation, "free" framing. Risk: countdown removal could cost 1-2pt (timer may have helped urgency-driven conversion); real_closed_trade adds reading time which could slow the 7s decision flow. Net: ~flat. |
| **Trust Seeker** (20%) | 50% | **52%** | **60%** | **66%** | V1 was Trust Seeker's best variant at 60%; V5 restores V1's trust stack (named wins + wins/losses + premium feel) while keeping V4's dark theme. Premium upgrades likely overcome the green-CTA penalty (which was muted by dark theme in V4 anyway). |
| **Weighted overall** | **44%** | **44%** | **51%** | **56%** | +0 to +12pt; median **+7pt** |

## The untested risk (now down to one element)

| Dimension | V5 value | Mechanism | If it fails |
|---|---|---|---|
| `trade_evidence` | `real_closed_trade` | Replaces 100%-Skeptical-flagged blurred_card with full disclosure (entry/exit/days/₹ gain) + "browse all" link for cherry-picking defense | Users read one disclosed trade as cherry-picked → suspicion shifts rather than resolves. Wins/losses disclosure mitigates by showing the full denominator (914W·62L). |

The other "untested" labels in v1's V5 — explicit_sla and CTA copy — are now classified more honestly: explicit_sla is a concretization of V4's existing implicit_refund (still requires Univest ops backing); CTA copy is an honest re-write of an existing element to match the actual 3-trade offer.

## Kill conditions (per segment)

- **Skeptical:** conversion < 27% after 2 weeks (mechanisms not transferring)
- **Curious Beginner:** conversion < 30% after 2 weeks (named-wins anchor not transferring to Univest's actual stock picks — this is the strongest out-of-matrix risk)
- **Bargain Hunter:** time-to-convert p50 > 10s (cognitive load increase from real_closed_trade reading time)
- **Trust Seeker:** conversion < 47% after 2 weeks (premium upgrades didn't compensate for any residual green-CTA penalty)

## Post-ship contingency (untested fallback — NOT a launch alternative)

**Swap cta_style: high_contrast_green → muted_premium** (dark teal). Use only if Trust Seeker conversion drops ≥ 5pt vs V4 over the first 2 weeks post-ship. At launch, V5 ships green-CTA only — V4 already demonstrated the dark-theme + green combo works (Trust Seeker recovered 40% → 50%).

## What changed from v1 of this synthesis

- **Untested-stack count: 3 → 1.** Most v1 "untested introductions" turned out to be V4 elements we missed in extraction. Confidence improves.
- **CTA copy: "See 1 real trade, free" → "See 3 real trades, free."** Matches the actual offer (the user flagged this hypothetically; screenshot verification proved the concern).
- **CTA stack: single → dual_outline_plus_sticky.** User chose Option B 2026-04-24 to preserve V4's self-segmentation mechanism and resolve mismatch via copy coherence.
- **Layout: full_screen → full_screen_dark.** V4 already uses dark theme.
- **NEW dimension: wins_losses_disclosure.** V1's "914 wins · 62 losses" transparency is the structural defense against cherry-picking; V5 adopts it.
- **Median predicted lift: +5.3pt → +7pt.** Better confidence in the synthesis, smaller untested stack.

---

*Source: `data/univest/synthesized_variant.json` (v2). Evidence basis: `data/univest/element_matrix.json` (v2, screenshot-validated) + `data/univest/weighted_scores.json` (v2) + overlay `.claude/rules/element-taxonomy-univest.md`.*

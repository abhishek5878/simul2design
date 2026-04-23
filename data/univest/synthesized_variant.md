# V5 — Synthesized variant for Univest ₹1 trial activation

> **Generated:** 2026-04-23. **Mode:** balanced. **Confidence:** medium.
> Predicted weighted-overall: **45.5% – 49.3% – 53.0%** vs V4 actual **44%** (+1.5 to +9pt, median +5.3pt).

This is the *synthesis*, not the *spec*. Adversary reviews this before spec-writer produces the buildable document. Do not hand to engineers yet.

## The V5 element set

| Dimension | V4 | **V5** | Evidence | Untested? |
|---|---|---|---|---|
| `layout` | full_screen | **full_screen** | Universal adoption (V2-V4). | — |
| `modal_interrupt` | no | **no** | friction: modal_interrupt 31/50 = 62% cross-segment in Control. | — |
| `branding` | none | **none** | V4's `none` outperformed V3's `crown_header`; safer without. | — |
| `price_visibility` | visible_primary | **visible_primary** | friction: price_opacity 39/50 = 78% in Control. | — |
| `cta_primary_label` | "Unlock FREE trade" | **"See 1 real trade, free"** | Overlay mechanism: honest framing removes V4's 33%-noticed "Unlock FREE vs ₹1" mismatch. | **untested** |
| `cta_style` | high_contrast_green | **high_contrast_green** | Clean V2→V3 contrast: **+6.42pt** weighted. Bargain +16, Curious +7, Skeptical +9, Trust **−10**. | — |
| `cta_stack` | dual_outline_plus_sticky | **single** | friction: dual_cta_label_mismatch 5/50 (10%) + element-level 33% noticed mismatch. | — |
| `urgency_mechanism` | none | **none** | friction: countdown_timer 6/12 (50% Skeptical) in V1; removed V2-V4. | — |
| `refund_or_guarantee_copy` | absent | **explicit_sla** ("Refund in 60s to source. No questions.") | 64% element-level cited refund as strongest pricing reassurance; explicit SLA strengthens. | **untested** (+ source-flag caveat) |
| `trust_signal` | implicit | **regulatory_plus_evidence** (regulator=sebi) | V1 was the only variant with this: Trust Seeker 60% (dataset max), Curious Beginner 27%. | — |
| `evidence_detail` | none | **named_past_outcome** (stock_named_with_rupee_gain) | 71% of V1 users cited a stock by name. Curious Beginner anchor quote: *"I bought it last year..."* | — |
| `trade_evidence` (overlay) | blurred_card | **real_closed_trade** (entry/exit/days/gain disclosed) | friction: blurred_card 12/12 (100% Skeptical) persistent V2-V4. Quote: *"Show me a real trade or don't."* | **untested** |

## Per-segment predictions

| Segment | V4 | V5 low | V5 point | V5 high | Primary drivers |
|---|---|---|---|---|---|
| Skeptical Investor (24%) | 25% | **30%** | **35%** | **40%** | real_closed_trade (removes 100% friction), explicit_sla, named_past_outcome, honest label |
| Curious Beginner (30%) | 33% | **36%** | **40%** | **44%** | named_past_outcome restored (ZOMATO-anchor mechanism), honest label |
| Bargain Hunter (26%) | 69% | **69%** | **71%** | **73%** | green CTA preserved (+16pt primary driver for this segment) |
| Trust Seeker (20%) | 50% | **48%** | **52%** | **56%** | regulatory_plus_evidence restored (V1 = 60% mechanism); green penalty (−10pt) retained |
| **Weighted overall** | **44%** | **45.5%** | **49.3%** | **53.0%** | |

## The three untested values (stacked risk)

| Dimension | V5 value | Mechanism | If it fails |
|---|---|---|---|
| `cta_primary_label` | "See 1 real trade, free" | Honest framing removes V4's 33%-noticed trust erosion | Users expect "actually free" and find a ₹1 step — mismatch shifts rather than resolves |
| `refund_or_guarantee_copy` | explicit_sla | 64% cite refund as strongest reassurance; concrete SLA closes Skeptical trust gap | "Refund in 60s" is not operationally true → bigger violation than absence |
| `trade_evidence` | real_closed_trade | Removes 100%-Skeptical-flagged blurred_card friction | Users read one disclosed trade as cherry-picking → suspicion shifts rather than resolves |

Three untested stacked. Each individually has a concrete mechanism argument. Combined interaction is unobserved; post-ship per-segment data is required to close the loop.

## Exploratory alternative (untested upgrade)

**Swap cta_style: high_contrast_green → muted_premium** (dark teal).

- Predicted: **46.5% – 50.3% – 54.0%** (median +1.0pt vs primary).
- Mechanism: preserve the +16/+7/+9 pt Bargain/Curious/Skeptical lift while removing the −10pt Trust Seeker green-penalty.
- Risk: stacks a fourth untested value. Only recommended for Trust-Seeker-heavy audiences or explicit exploratory runs.

## Kill conditions

Predicted conversion collapses to V4 or below if:
- **Skeptical:** real_closed_trade reads as cherry-picking, OR the SLA is not operationally true.
- **Curious Beginner:** the stocks named in the carousel don't resonate with this cohort, OR trade card displaces the carousel visually.
- **Bargain Hunter:** added trust/evidence elements slow the 7-second decision flow.
- **Trust Seeker:** the restored trust signals don't offset the green penalty (switch to muted_premium if observed).

## What happens next

1. **Adversary agent** (IDEA.md Day 5) challenges each of these 12 choices.
2. Synthesize re-runs with revisions.
3. **estimate-conversion** refines the intervals using per-segment Wilson confidence bands.
4. **spec-writer** produces the buildable document (this is NOT the spec — it's the decision set).

---

*Source: `data/univest/synthesized_variant.json`. Evidence basis: `data/univest/weighted_scores.json` + `data/univest/element_matrix.json` + overlay `.claude/rules/element-taxonomy-univest.md`.*

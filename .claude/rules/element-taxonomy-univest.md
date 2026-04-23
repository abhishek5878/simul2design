# Element taxonomy — Univest overlay

Client-specific extensions to `.claude/rules/element-taxonomy-base.md` for the Univest activation-screen engagement. Every variant mapping lives here; the base file stays client-neutral.

Version: 1.0. Pairs with `data/univest/element_matrix.json`.

## Client context

Univest is an India-regulated fintech advisory product. The simulation targets the ₹1 trial activation screen — the gating surface where a prospect decides to unlock one real trade recommendation for ₹1 (with refund). SEBI-regulated context, Indian-rupee-denominated trial, trust signals anchor on regulatory compliance and past stock-pick outcomes.

## Overlay values (specific to this client's taxonomy)

### `trust_signal` (extends base)
- Base values apply.
- When `trust_signal` is `regulatory` or `regulatory_plus_evidence`: specify `regulator=sebi` (SEBI is the Indian securities regulator).

### `evidence_detail` (extends base)
- Base values apply.
- When `evidence_detail` is `named_past_outcome`: Univest-observed values are `stock_named_with_rupee_gain` (e.g., "ZOMATO +₹23,435 in 3 days"). This specific format is Univest's pattern and drove a 71% "cited a stock by name" signal in V1.

### `cta_primary_label` (Univest-observed strings)
- `"Start Trial Now"` (Control)
- `"Unlock FREE trade"` (V4)
- `"₹1 Trial" / "Activate for ₹1"` (V1, inferred for V2/V3 — see Extraction confidence)
- `"See 1 real trade, free"` — proposed for V5 per IDEA.md, never tested

## Univest-only dimensions

### `trade_evidence` (Univest-specific; not in base)
- Concrete disclosure of past trade performance, a Univest-native concept (fintech advisory).
- `none` — no trade shown
- `blurred_card` — trade card redacted or teaser
- `real_closed_trade` — fully disclosed closed trade (entry / exit / days held / ₹ gain) **[proposed but not tested]**

Rationale for overlay (not base): `trade_evidence` is meaningful only for products that show historical trade outcomes as part of activation. For a SaaS signup page this dimension doesn't exist. If a second fintech client surfaces this, consider whether it generalizes to a base dimension like `concrete_outcome_evidence`.

## Variant → (dimension, value) mapping for Univest

| Dimension | Control | V1 | V2 | V3 | V4 |
|---|---|---|---|---|---|
| `layout` | `bottom_modal` | `full_screen_dark` | `full_screen` | `full_screen` | `full_screen` |
| `modal_interrupt` | `yes` | `no` | `no` | `no` | `no` |
| `branding` | `none` | `none` | `crown_header` | `crown_header` | `none` |
| `price_visibility` | `opaque` | `visible_primary` | `visible_with_framing` | `visible_with_framing` | `visible_primary` |
| `cta_primary_label` | `"Start Trial Now"` | `"Activate for ₹1"` | `"Activate for ₹1"` (inferred) | `"Activate for ₹1"` (inferred) | `"Unlock FREE trade"` |
| `cta_style` | `neutral_default` | `neutral_default` | `low_contrast_subordinate` | `high_contrast_green` | `high_contrast_green` |
| `cta_stack` | `single` | `single` | `single` | `single` | `dual_outline_plus_sticky` |
| `urgency_mechanism` | `none` | `countdown_timer` | `none` | `none` | `none` |
| `refund_or_guarantee_copy` | `absent` | `absent` | `implicit_refund` | `implicit_refund` | `absent` |
| `trust_signal` | `implicit` | `regulatory_plus_evidence` (regulator=sebi) | `implicit` | `implicit` | `implicit` |
| `evidence_detail` | `none` | `named_past_outcome` (stock_named_with_rupee_gain) | `none` | `none` | `none` |
| `trade_evidence` (overlay) | `none` | `none` | `blurred_card` | `blurred_card` | `blurred_card` |

## Extraction confidence

| Variant.Dimension | Confidence | Note |
|---|---|---|
| V2.cta_primary_label | inferred | Source shows banner "Activate @ ₹1 & get instant refund" but not the button label. Inferred as "Activate for ₹1" by parallel to V1. |
| V3.cta_primary_label | inferred | Same as V2 — V3 is V2 + high-contrast-green, no CTA-label change stated. |

## Univest-specific contradictions (informs future `detect-conflicts` rule file)

### Segment-conflict rules (apply per-segment penalty)

- `urgency_mechanism=countdown_timer` + segment `skeptical_investor` → negative. V1 evidence: 6/50 flagged timer as manipulation; per IDEA.md, timer alienated 41% of Skeptical Investors.
- `trade_evidence=blurred_card` + segment `skeptical_investor` → negative. V2/V3/V4 persistent friction: 12/50 flagged blurred card as gimmick.
- `cta_style=high_contrast_green` + segment `trust_seeker` → negative. V2→V3 contrast: −10pts (50% → 40%). Premium-tone regression.
- `branding=crown_header` + `cta_style=low_contrast_subordinate` → negative hierarchy. V2 evidence: 22% of users missed the CTA entirely or tapped the banner mistakenly.
- `cta_stack=dual_outline_plus_sticky` with mismatched labels ("Unlock FREE trade" outline vs "₹1 Trial" sticky) → friction. V4: 33% notice the mismatch, 5/50 flag as deceptive. Not a hard contradiction but a trust cost.

### Cross-dimension consistency rules (structural — synthesize must enforce)

- **Shared-banner pair:** `price_visibility=visible_with_framing` IS the banner that also displays `refund_or_guarantee_copy` content. They refer to the same on-screen element.
  - Required: if `price_visibility=visible_with_framing`, then `refund_or_guarantee_copy ∈ {implicit_refund, explicit_sla, no_questions_asked}` (non-absent).
  - Required: if `price_visibility=visible_primary` (no banner), then `refund_or_guarantee_copy=implicit_refund` is INCONSISTENT unless spec-writer places refund copy as a separate visual element (e.g., `RefundSlaLine` below the CTA). Flag to spec-writer.
  - Forbidden combo: `price_visibility=visible_with_framing` + `refund_or_guarantee_copy=absent` — a framing banner with no refund semantics has nothing to frame.
  - Rationale: in the Univest V2/V3 data these two co-vary perfectly because they are two taxonomy projections of one banner element. The rule makes this explicit so synthesize never emits inconsistent combinations.

- **Trust-evidence pair:** if `trust_signal ∈ {regulatory, evidence_mode, regulatory_plus_evidence}`, then `evidence_detail ≠ none`.
  - Rationale: a trust signal claiming "evidence" with no evidence detail is an empty container.

- **Trade-evidence / evidence-detail non-overlap:** if `trade_evidence=real_closed_trade` AND `evidence_detail=real_outcome_disclosure`, flag as potential redundancy — both display full trade disclosure. Synthesize should pick at most one as the primary disclosure surface.

- **Label-matches-flow:** if `cta_primary_label` contains the word "free" AND the subsequent flow requires payment before the advertised experience, the label is deceptive. Adversary obj-001 failure mode. This is an OPERATIONAL rule, not purely an element-pair rule — spec-writer must surface it as a precondition.

- **Trade-evidence operational disclosure:** `trade_evidence=real_closed_trade` + Indian fintech client → past-performance disclaimer required (SEBI rule). spec-writer must include the disclaimer copy; contradicts the "abstract metrics alienate" friction at the disclaimer level unless kept minimal.

## Proposed-but-untested values (available to synthesize; must be flagged in output)

The taxonomy-base values below exist so `synthesize` can propose them, but Univest's simulation has zero observation data on them. Any V5 decision that uses one of these must be accompanied by an explicit "untested in this dataset" note in the spec and a widened confidence interval from `estimate-conversion`.

- `cta_style=muted_premium` — proposed as dark-teal alternative to `high_contrast_green`, expected to preserve conversion for Bargain Hunter while removing the Trust Seeker premium-feel penalty.
- `refund_or_guarantee_copy=explicit_sla` — proposed as "Refund in 60s to source. No questions." to close the Skeptical Investor trust gap.
- `trade_evidence=real_closed_trade` — proposed disclosure format to replace blurred_card; removes the persistent 12/50 Skeptical Investor friction.
- `cta_primary_label="See 1 real trade, free"` — proposed honest framing for V4's dual-CTA mismatch.

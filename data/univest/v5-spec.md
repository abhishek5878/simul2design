# V5 — Buildable spec for Univest ₹1 trial activation (v2 — screenshot-validated)

> **Source evidence:** [element_matrix.json](./element_matrix.json) (v2) • [weighted_scores.json](./weighted_scores.json) (v2) • [synthesized_variant.json](./synthesized_variant.json) (v2) • [adversary_review.json](./adversary_review.json) (v2) • [conversion_estimates.json](./conversion_estimates.json) (v2) • [source-screenshots/](./source-screenshots/) (immutable)
> **Generated:** 2026-04-24 (supersedes 2026-04-23)
> **Predicted weighted-overall conversion:** **51%** (mechanism range **45–56%**, Wilson envelope 22–74%). Baseline: V4 at 44%. **Median lift +7pt.**

---

## 0. Executive summary

**The decision: ship V5.** Seven element changes from V4. Predicted weighted-overall **51%** vs V4's 44% — **+7pt median**. Confidence **medium** (downgraded from medium-high because simulator-LLM provenance is undisclosed; see §9.4).

The v2 re-extraction (screenshots) revealed that most of V5's "new elements" were already present in V4 — refund copy, SEBI badge, crown branding, aggregate metrics. **V5's actual value-add is narrower and more defensible**: replace blurred trade card with real disclosed trade, **adopt V1's wins/losses transparency**, remove the manipulation-perceived countdown timer, concretize the vague refund copy, and fix the dual-CTA copy mismatch by matching the actual offer count (3 free trades, not 1).

**Why each audience segment activates:**

| Segment | Weight | V4 → V5 | Why they activate (audience reasoning + evidence) |
|---|---|---|---|
| **Skeptical Investor** | 24% | 25% → **35%** | Five trust barriers removed simultaneously: blurred trade card → real closed trade with full disclosure; vague "instant refund" → explicit "Refund in 60s to source"; missing wins/losses ratio → V1's "914 wins · 62 losses" transparency adopted (defeats cherry-picking structurally); "04:34 Left" countdown removed (41% of segment flagged as manipulation); CTA copy made coherent with the actual 3-trade offer. Source quote (12/12 = 100% segment): *"Show me a real trade or don't"* — V5 answers literally. |
| **Curious Beginner** | 30% | 33% → **41%** | V1's named-stock carousel (TMPV, ZOMATO +₹23,435, RELIANCE) restored. *"I bought it last year — if they nailed that, I should listen"* anchor mechanism. **71% of V1 users cited a stock by name**; V2-V4 dropped this and lost the segment's primary anchor. |
| **Bargain Hunter** | 26% | 69% → **69%** (≈flat) | V4's strongest elements preserved at full strength: high-contrast green sticky CTA (+16pt observed for this segment), dual-CTA self-segmentation that contributed to V4's 44% lift, "free" framing in outline copy, ~7-second decision flow protected. Risk: countdown-timer removal could cost 1-2pt; real_closed_trade adds reading time. Net: ~flat. |
| **Trust Seeker** | 20% | 50% → **60%** | V1 was Trust Seeker's best at 60%. V5 restores V1's full trust stack (named wins + wins/losses transparency + SEBI prominence) while keeping V4's dark theme that already muted the green-CTA premium-feel penalty. Premium upgrades likely overcome any residual penalty. |

**The four levers that drive the +7pt, in evidence-strength order:**

1. **Real closed trade card** + **wins/losses disclosure** (paired) — V5's structural answer to the cherry-picking adversary objection. The disclosure ("914 wins · 62 losses") shows the full denominator; the closed trade shows the front of the win pile. Skeptical Investor's persistent friction is removed at both the aggregate AND the instance level.
2. **Restored V1 named-wins carousel** (TMPV, ZOMATO +₹23,435, RELIANCE) — the Curious Beginner anchor mechanism V2-V4 dropped.
3. **CTA copy coherence** — outline "See 3 real trades, free" (matches the banner's actual offer count) + sticky "Activate for ₹1." Resolves V4's 33%-noticed mismatch friction without removing the dual-CTA structure that drove V4's lift.
4. **Concretize refund + remove countdown** — "Refund in 60s to source. No questions." replaces V4's vague "instant refund." Countdown timer removed (Skeptical-only friction with no demonstrated cross-segment lift).

**Ship gate.** Two operational preconditions in §4 must be signed off (legal + ops). Down from 4 in v1; the corrected matrix removed 2 design-blockers that v1 raised (V4 already has the elements v1 V5 was "introducing").

---

## 1. Changes from V4 — the corrected diff

### 1.1 `trade_evidence` — V4 `blurred_card` → V5 `real_closed_trade`

- **What changes:** Replace the blurred Live Trade card (stock name / entry price / target price hidden) with a fully disclosed Closed Trade card. Stock name, entry price, exit price, days held, absolute rupee gain — all visible. Plus a "Browse all recent trades (mixed outcomes)" link for cherry-picking defense.
- **Replaces component:** `BlurredTradeCard` (Univest's current Live Trades card with values blurred).
- **New component:** [`ClosedTradeCard`](#21-closedtradecard) — see §2.
- **Citation:** `friction_points.blurred_card_alienates_skeptics` — *"12/12 (100% of Skeptical segment) flagged blurred card as gimmick. Persistent across V2/V3/V4."* Quote: *"Show me a real trade or don't."*
- **Per-segment expected impact:** Skeptical +5pt (after coupling discount). Other segments: neutral.
- **Untested:** yes — no observed datapoint for this exact UI. Mechanism is strong; the wins/losses disclosure (§1.5) provides additional structural defense.

### 1.2 `wins_losses_disclosure` — V4 `no` → V5 `yes` (NEW dimension)

- **What changes:** Add V1's transparency display: "All-time accuracy 84.7% (**914 wins · 62 losses**)" prominently shown alongside the SEBI badge. V2/V3/V4 dropped this (kept only the 84.7% claim without the denominator).
- **Replaces component:** none (V4 has SEBI + 85%+ but no wins/losses ratio).
- **New component:** [`WinsLossesDisclosure`](#22-winslossesdisclosure) — see §2.
- **Citation:** `matrix.variants.V1.elements.wins_losses_disclosure` — *"V1 prominently displays '914 wins · 62 losses' alongside the 84.7% accuracy claim. V1 is the only variant with this transparency. Critical defense against cherry-picking concerns."*
- **Per-segment expected impact:** Skeptical +3pt, Trust Seeker +3pt (premium transparency).
- **Untested as introduction:** observed in V1 (confounded with V1's other trust elements); not isolable but mechanism is structurally strong.

### 1.3 `evidence_detail` — V4 `aggregate_metric` → V5 `aggregate_plus_named`

- **What changes:** Restore V1's named-wins carousel (TMPV +12.93%, ZOMATO +₹23,435 closed in 3 days, RELIANCE +12.93%) to coexist with V4's existing aggregate metrics (85%+ Accuracy, 3500+ Profitable Trades). Both formats serve different segments.
- **Replaces component:** V4 has only the aggregate row.
- **New component:** [`PastWinsCarousel`](#23-pastwinscarousel) — see §2. Sits between the aggregate metrics row and the new ClosedTradeCard.
- **Citation:** *"71% of V1 users cited a stock by name."* Quote: *"I bought it last year — if they nailed that, I should listen."* (Curious Beginner V1 reaction to ZOMATO win.)
- **Per-segment expected impact:** Curious +5pt, Trust Seeker +5pt.
- **Untested:** no — observed in V1.

### 1.4 `urgency_mechanism` — V4 `countdown_timer` → V5 `none`

- **What changes:** Remove the "04:34 Left" countdown timer from the price+refund banner. The banner keeps the price and refund copy; the timer disappears.
- **Replaces component:** `CountdownTimerBadge` in the banner (V1-V4 all had it — corrected from v1 spec which thought V4 didn't).
- **New component:** none (removal).
- **Citation:** `friction_points.countdown_timer_manipulation` — *"6/50 users (41% of Skeptical Investors) flagged countdown as manipulation. Persistent across V1-V4 per screenshot re-extraction."*
- **Per-segment expected impact:** Skeptical +3pt, Trust Seeker +2pt, Curious +1pt, Bargain -2pt (timer may have helped urgency-driven conversion).
- **Untested as removal:** yes — no observed variant in the dataset removes the timer. V5 is the first.

### 1.5 `refund_or_guarantee_copy` — V4 `implicit_refund` ("Activate @ ₹1 & Get instant refund") → V5 `explicit_sla` ("Refund in 60s to source. No questions.")

- **What changes:** Replace the vague "Get instant refund" copy with a specific operational commitment: "Refund in 60s to source. No questions." (Per-payment-method SLA matrix in §4.)
- **Replaces component:** the refund text inside `PriceRefundBanner` — the banner element exists in V2/V3/V4 (corrected from v1 which thought V4 had no refund copy).
- **Updated component:** [`PriceRefundBanner`](#24-pricerefundbanner) — see §2 (modified, not new).
- **Citation:** Element-level note — *"64% cited refund clause as strongest pricing reassurance."*
- **Per-segment expected impact:** Skeptical +2pt, Trust Seeker +1pt.
- **Untested as concretization:** yes — but lower-risk than v1 thought, because V4 already has implicit_refund as a baseline.

### 1.6 `cta_primary_label` (outline) — V4 `"Unlock FREE trade"` → V5 `"See 3 real trades, free"`

- **What changes:** The outline CTA label changes to match the actual offer count (banner says "Claim 3 FREE Trades"; old V4 outline said singular "Unlock FREE trade" — that's the 33%-noticed mismatch).
- **Replaces component:** `OutlineCtaButton.label` prop.
- **Citation:** `matrix.flags.cta_inconsistency` — *"Banner says '3 FREE Trades' but outline CTA says 'Unlock FREE trade' (singular). Internal copy inconsistency, contributes to dual_cta_label_mismatch friction (33% noticed in V4)."*
- **Per-segment expected impact:** Cross-segment +1pt (removes mismatch friction).
- **Untested:** copy is untested but the mechanism (label-matches-banner) is straightforward.
- **Operational requirement:** the outline CTA flow MUST actually deliver 3 free trades pre-payment (Operational Precondition 1).

### 1.7 `cta_secondary_label` (sticky) — V4 `"Start FREE Trial @ ₹1"` → V5 `"Activate for ₹1"`

- **What changes:** Sticky CTA label simplified — the outline already carries the "free" message; the sticky now carries only the activation commitment.
- **Replaces component:** `StickyCtaButton.label` prop.
- **Citation:** Overlay mechanism — clean dual-CTA hierarchy.
- **Per-segment expected impact:** Cross-segment +0 to +1pt.
- **Untested:** copy is untested; mechanism is straightforward separation-of-concerns.

### Unchanged from V4 (preserved correctly per v2 re-extraction)

`layout=full_screen_dark`, `modal_interrupt=no`, `branding=crown_header`, `price_visibility=visible_with_framing`, `cta_style=outline_on_dark_plus_sticky_green`, `cta_stack=dual_outline_plus_sticky`, `trust_signal=regulatory_plus_evidence (sebi)`, the `aggregate_metric` portion of evidence_detail (V5 ADDS named to the existing aggregate, doesn't replace).

> **Adversary obj-005 — Trust Seeker green-CTA risk.** V5 ships with green sticky on dark theme (V4 already demonstrated this combo recovers Trust Seeker from V3's green-on-light penalty). Post-ship contingency: if Trust Seeker conversion drops ≥ 5pt vs V4 over 2 weeks, switch to muted dark-teal sticky (mockup at [`design/v5b-muted-premium.png`](./design/v5b-muted-premium.png)). Sequenced contingency, not parallel A/B. See §7.

---

## 2. Component specifications

### 2.1 ClosedTradeCard

**Purpose:** Replace V4's `BlurredTradeCard` (Live Trades section). The single most-frequently-rendered evidence component.

**Fields:**
- `stock_name: string` — verbatim ticker (e.g., `"ZOMATO"`)
- `entry_price: number` (₹)
- `exit_price: number` (₹)
- `days_held: number`
- `absolute_gain_inr: number` (positive — this is a winning trade)
- `closed_at_iso: string` — for the "Closed N days ago" relative timestamp
- `subscriber_tier: string` — defensive against showing trades only available to higher tiers
- `is_disclosed_for_compliance: boolean` — SEBI past-performance disclaimer required if true (always true for India; see §4)

**Data contract:**
```
GET /api/v1/trades/closed?
    limit=1
    &filter=outcome:win
    &max_age_hours=24
    &subscriber_tier=trial_eligible
    &order_by=recency_desc
```
- Cache: 5min stale-while-revalidate.
- Fallback if no eligible trade in 24h: hide the card entirely (do NOT show a stale trade).
- Fallback if API fails: hide the card and log `v5_closed_trade_card_hidden{reason: "api_error"}`.

**Visual design:**
- Card background: light surface on the dark theme (white/off-white box on the dark navy page).
- Stock name + closed-N-days-ago timestamp at top.
- "+₹{absolute_gain_inr}" in green, large.
- Entry / Exit / Days held in a 3-column row.
- Below the card: a text link "Browse all recent trades (mixed outcomes) →" pointing to `/trades/recent` — visible cherry-picking defense.
- Compliance disclaimer below: "Past performance is not indicative of future returns. SEBI INH000013776." — small but legible.

**Acceptance criteria:**
- AC1: card renders with all 5 fields populated, no nulls.
- AC2: if any field missing, card does not render and `v5_closed_trade_card_hidden{reason:"data_incomplete"}` fires.
- AC3: "Browse all" link is keyboard-tabbable.
- AC4: compliance text is at least 11px and contrast ratio ≥ 4.5:1.

### 2.2 WinsLossesDisclosure

**Purpose:** Display V1's transparency format adapted for the v2 metrics. Sits in the trust-evidence row alongside SEBI badge.

**Fields:**
- `accuracy_percent: number` (e.g., `84.7`)
- `wins_count: number` (e.g., `914`)
- `losses_count: number` (e.g., `62`)
- `period_label: string` (e.g., `"All-time"` or `"Last 12 months"`)

**Data contract:**
```
GET /api/v1/stats/track_record?period=all_time
```
- Refresh: daily; cache 24h.
- If `wins_count + losses_count == 0` → hide entire row (cannot make claim without denominator).

**Visual design:**
- Row format: "All-time accuracy **84.7%**" (bold) + small gray subtext "(914 wins · 62 losses)"
- Position: in the trust-evidence row, between the SEBI badge column and the "3500+ Profitable Trades" column. Replaces V4's "85%+ Accuracy Rate" cell with the more honest version.

**Acceptance criteria:**
- AC1: losses count is visible at the same prominence as wins count (no font-size discrimination).
- AC2: total-sample (wins+losses) is what gets reported as the denominator; cannot show wins without showing losses.

### 2.3 PastWinsCarousel

**Purpose:** Restore V1's named-wins carousel — the Curious Beginner anchor.

**Fields per item:**
- `stock_name: string`
- `gain_format: "percent" | "absolute_inr" | "both"`
- `gain_value: number`
- `closed_at_iso: string`
- `closed_descriptor: string` (e.g., `"Closed same day"`, `"Closed in 3 days"`)

**Data contract:**
```
GET /api/v1/trades/top_recent_wins?limit=5&max_age_days=7
```
- Refresh: hourly.
- Fallback if fewer than 3 results: hide carousel.

**Visual design:**
- Horizontal-scroll row of 3-5 cards.
- Each card: stock name (top), "+12.93%" or "+₹23,435" (mid, green), "Net Gain · Closed N days ago" (subtext).
- Position: between the trust-evidence row and the ClosedTradeCard.

**Acceptance criteria:**
- AC1: at least 3 cards render or carousel is hidden.
- AC2: "Closed N days ago" is computed at render time, not stored.
- AC3: tapping a card opens `/trades/{stock}/{trade_id}` (audit trail).

### 2.4 PriceRefundBanner (modified)

**Purpose:** V4 already has this banner ("Activate @ ₹1 & Get instant refund · 04:34 Left"). V5 modifies: keep price + refund framing; **REPLACE refund copy with explicit SLA**; **REMOVE countdown timer**.

**Fields:**
- `price: number` (₹1)
- `refund_sla_text: string` — verbatim: `"Refund in 60s to source. No questions."`
- (countdown_text field deleted)

**Visual design:**
- Banner: dark blue background, white text.
- Top line: "**Claim 3 FREE Trades →**" (preserved from V4, links to outline CTA).
- Bottom line: "Activate @ ₹1 — **Refund in 60s to source. No questions.**"
- No countdown badge in upper-right.

**Acceptance criteria:**
- AC1: refund SLA text matches Operational Precondition 2's per-payment-method matrix (if any payment method's SLA exceeds 60s, copy must change).
- AC2: no countdown element renders.

### 2.5 DualCtaStack (preserved structure, copy fixed)

**Purpose:** V4 has dual; V5 keeps the dual structure (per user decision Option B 2026-04-24). Copy fixed for coherence.

**Outline CTA (top of viewport, above ClosedTradeCard):**
- Label: `"See 3 real trades, free"`
- Style: outline button, green border + green text, transparent fill (works on dark theme)
- Tap → routes to `/trades/free-preview` showing 3 closed trades pre-payment (Operational Precondition 1).

**Sticky CTA (bottom of viewport):**
- Label: `"Activate for ₹1 →"`
- Style: solid green fill (high_contrast_green), white text. Sticky to bottom of viewport.
- Tap → routes to `/checkout/trial?amount=1` (existing flow).

**Acceptance criteria:**
- AC1: outline CTA label matches banner offer count exactly (both say "3").
- AC2: tapping outline CTA must NOT route to a payment screen (Op Precondition 1 — kill-condition `v5_payment_required_before_trade` fires immediately if violated).
- AC3: sticky CTA flow is unchanged from V4's existing ₹1 trial activation.

---

## 3. Copy book (verbatim — engineer must match exactly)

| Element | Copy (verbatim) |
|---|---|
| Banner top line | `Claim 3 FREE Trades →` |
| Banner bottom line | `Activate @ ₹1 — Refund in 60s to source. No questions.` |
| Outline CTA label | `See 3 real trades, free` |
| Sticky CTA label | `Activate for ₹1 →` |
| Trust row column 1 | `SEBI Reg. INH000013776` |
| Trust row column 2 | `All-time accuracy 84.7% (914 wins · 62 losses)` |
| Trust row column 3 | `3500+ Profitable Trades` |
| Closed trade card disclaimer | `Past performance is not indicative of future returns.` |
| Browse all link | `Browse all recent trades (mixed outcomes) →` |

---

## 4. Operational preconditions (hard prerequisites)

V5 is design-complete. These two operational commitments are required before ship:

### Precondition 1 — "Free" flow actually delivers 3 free trades pre-payment
- **What:** The outline CTA `See 3 real trades, free` must route to a flow that shows 3 closed trades without requiring any payment, account creation friction, or paywall.
- **Why:** If the user taps "See 3 real trades, free" and sees a payment screen, the copy is deceptive — bigger trust violation than V4's mismatched-but-vague labels.
- **Owner:** Product + engineering.
- **Verifiable by:** Integration test that taps outline CTA and asserts no payment screen, KYC screen, or signup gate fires before 3 trades are shown.

### Precondition 2 — Refund SLA per payment method matches the copy
- **What:** "Refund in 60s to source. No questions." must be operationally true for every payment method Univest accepts. If UPI is 30s but card is 5 days, the SLA copy must be revised before ship to either (a) generic weaker copy, or (b) per-payment-method conditional copy.
- **Owner:** Operations + payments team + legal.
- **Verifiable by:** SLA matrix doc showing observed p90 refund elapsed-time per payment method over the past 30 days. Submit before ship.

> Two preconditions, down from 4 in v1. The corrected matrix removed two design-blockers v1 raised (V4 already has the elements v1 V5 was "introducing").

---

## 5. Instrumentation

Every kill-condition from `conversion_estimates.json` becomes an observation event.

| Event name | Trigger | Properties | Kill threshold |
|---|---|---|---|
| `v5_activation_impression` | Activation screen rendered | `segment_inferred`, `viewport_height` | — baseline |
| `v5_closed_trade_card_rendered` | `ClosedTradeCard` appears | `stock_name`, `trade_age_hours`, `is_win` | **Kill Skeptical** if `trade_age_hours > 24` rate > 5% |
| `v5_closed_trade_card_hidden` | Fallback fired | `reason` (`no_recent_win` / `api_error` / `data_incomplete`) | **Kill Skeptical** if hidden rate > 20% |
| `v5_browse_all_trades_clicked` | User taps "Browse all" link | `segment_inferred` | **Watch obj-003** — if engagement < 5%, cherry-picking mitigation didn't reach users |
| `v5_outline_cta_clicked` | User taps "See 3 real trades, free" | `segment_inferred` | — |
| `v5_trade_shown_before_payment` | Free-preview route renders 3 trades | `count`, `time_to_render_ms` | **Kill obj-001** if count != 3 OR time > 5s |
| `v5_payment_required_before_trade` | Payment screen shows before any trade is rendered | (binary) | **Stop-ship immediately** — Precondition 1 broken |
| `v5_sticky_cta_clicked` | User taps "Activate for ₹1" | `segment_inferred`, `time_to_convert_seconds` | **Kill Bargain** if `time_to_convert_seconds` p50 > 10s |
| `v5_refund_issued` | Refund completed | `payment_method`, `elapsed_seconds` | **Kill Precondition 2** if p90 elapsed_seconds > 60 for ≥ 1 week |
| `v5_named_stock_recall_post_test` | Post-conversion survey: "What stock was named?" | `correct_recall_pct` by segment | **Kill Curious obj-008** if Curious correct_recall < 10pt above pre-test baseline |
| `v5_conversion` | ₹1 subscription started | `segment_inferred` | **Kill Trust Seeker** if Trust < 47% over 2 weeks (switch to muted_premium per §7) |
| `v5_cohort_ltv_30d` | 30 days post-activation | cohort-level | **Watch** if cohort LTV ≥ 20% below V4 |

---

## 6. Predicted conversion (v2)

From [conversion_estimates.json](./conversion_estimates.json) (v2). Wilson 95% intervals + coupling discount on Skeptical.

| Segment | n | V4 actual | V5 low | V5 point | V5 high | Primary kill-condition |
|---|---|---|---|---|---|---|
| Skeptical Investor | 12 | 25% | **9%** | **35%** | **62%** | Skeptical conv ≤ 27% after 2 weeks |
| Curious Beginner | 15 | 33% | **15%** | **41%** | **65%** | Carousel named-stock recall < 10pt above pre-test |
| Bargain Hunter | 13 | 69% | **42%** | **69%** | **87%** | Time-to-convert p50 > 10s OR conversion drops > 5pt vs V4 |
| Trust Seeker | 10 | 50% | **24%** | **60%** | **83%** | Trust Seeker < 47% (switch to muted_premium) |
| **Weighted overall** | — | **44%** | **22.3%** | **50.6%** | **73.8%** | — |
| **Mechanism-derived headline range** | — | **44%** | **45%** | **51%** | **56%** | — |

> **Why two ranges:** the **Wilson envelope [22.3%, 73.8%]** is the honest small-sample reality at n=10-15 per segment. The **mechanism-derived band [44%, 56%]** is the practical decision-grade range — what V5 will produce if the synthesis is correct. The Wilson envelope is wider because n=10 baselines just are wide; the mechanism band is narrower because the synthesis adds structure.

---

## 7. Rollout recommendation

**Single-design ramp (no parallel A/B at launch):**
V5 ships green sticky CTA on dark theme (V4 already demonstrated this combo recovers Trust Seeker from V3's green-on-light penalty: V3 40% → V4 50%).

**Ramp schedule:**
- Week 1: 10% of activation traffic on V5, 90% on V4 (holdout). Enable Section 5 instrumentation.
- Week 2: 50/50 split. Watch kill thresholds.
- Week 3: 100% V5 if no kill-condition tripped AND no Precondition-2 alarm.

**Post-ship contingency (NOT a launch alternative):**
If Trust Seeker conversion drops ≥ 5pt vs V4's 50% over 2 weeks (i.e. lands at ≤ 45%), pause the ramp and switch to muted dark-teal sticky CTA. Mockup pre-rendered at [`design/v5b-muted-premium.png`](./design/v5b-muted-premium.png). Sequenced contingency, not parallel A/B.

**Stop-ship criteria (immediate rollback):**
- `v5_payment_required_before_trade` fires at all (Precondition 1 broken).
- `v5_closed_trade_card_hidden` rate > 20% for 24h.
- Legal retracts approval on SEBI past-performance disclaimer copy.
- Any segment conversion underperforms V4 by > 5pt over 2 weeks.

---

## 8. What this spec deliberately does NOT prescribe

- **Stock selection for `ClosedTradeCard` and `PastWinsCarousel`**: the engine specifies the data contracts but not which specific stocks should win the cards. Default rule is `most recent eligible win, last 24h` for the card and `top 5 closed wins, last 7 days` for the carousel. Personalization to user's watchlist is an untested upgrade for V5.1.
- **Exact wording of "Browse all recent trades (mixed outcomes)"**: copy team has latitude. Mechanism: visible cherry-picking-defense link.
- **Per-payment-method refund SLA matrix**: spec requires it exists but the actual numbers are an ops commitment.
- **Compliance disclaimer wording**: legal-team-owned. Spec provides a default that's SEBI-compliant; legal can revise.

---

## 9. Cross-references and caveats

- [synthesized_variant.md](./synthesized_variant.md) (v2) — narrative V4 vs V5 for PM review.
- [adversary_review.json](./adversary_review.json) (v2) — full structured objections (0 blockers, 2 operational preconditions, 4 should-fix, 1 watch).
- [conversion_estimates.json](./conversion_estimates.json) (v2) — Wilson intervals, coupling math, per-segment kill-conditions.
- [element_matrix.json](./element_matrix.json) (v2 — screenshot-validated).
- [source-screenshots/](./source-screenshots/) — immutable reference images for all 5 variants.

**Caveats:**

1. **Source simulation persona definitions are abstract archetypes**, not voice-of-customer-grounded. The 5 segments ("Skeptical Investor," etc.) are simulation constructs. If Univest can hand over real user-research data (app-store reviews, churn surveys, support tickets), V5 confidence intervals tighten retroactively. Filed in `tasks/improvements.md`.

2. **Segment weights** (Skeptical 24%, Curious 30%, Bargain 26%, Trust 20%) come from the simulation's persona composition. If Univest's actual user base differs, re-run `weigh-segments` + `synthesize` with override weights.

3. **Confidence is medium**, not high. The binding constraint is sample size in the source simulation (n=10-15 per segment). Future simulations should target n ≥ 30 per segment to narrow the Wilson bands.

4. **Simulator-LLM calibration is itself a source of uncertainty.** Per Seshadri et al., "Lost in Simulation," 2026 (arxiv:2601.17087), LLM-simulated user evaluations vary by up to 9pt across simulator LLMs and systematically *under-estimate* hard segments / *over-estimate* medium ones. Concrete implication: the wide low-tier (Wilson 22.3%) and the kill-switch architecture in §5–7 are structural responses to this known miscalibration. The post-ship `sim-flow record-actuals` loop closes the calibration gap over time. See [../../tasks/related-work.md](../../tasks/related-work.md) §1. Apriori does not disclose its simulator LLM; provenance flagged as `unknown` in conversion_estimates.json.

5. **v2 supersedes v1.** The original 2026-04-23 extraction relied on the source page's prose descriptions, which omitted multiple visual elements present in V4 (refund banner, countdown, crown branding, SEBI badge, aggregate metrics). Screenshots saved as immutable artifacts at `source-screenshots/` are the new ground truth. Lesson logged in `tasks/lessons.md`.

---

*Spec generated by the Multiverse Synthesis Engine. v2 of the engine, v2 of the V5 design for Univest activation screen.*

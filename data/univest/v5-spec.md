# V5 — Buildable spec for Univest ₹1 trial activation

> **Source evidence:** [element_matrix.json](./element_matrix.json) • [weighted_scores.json](./weighted_scores.json) • [synthesized_variant.json](./synthesized_variant.json) • [adversary_review.json](./adversary_review.json) • [conversion_estimates.json](./conversion_estimates.json)
> **Generated:** 2026-04-23
> **Predicted weighted-overall conversion:** **48.6%** (Wilson 95% band 22.3% – 52.0%). Baseline: V4 at 44%.

---

## 0. Executive summary

V5 replaces six elements of Univest's ₹1 trial activation screen to restore V1's trust-signaling strengths while keeping V4's conversion-oriented CTA style and removing V4's 33%-noticed "Unlock FREE trade" / "₹1 Trial" label mismatch. Primary levers: **real closed trade card** (replacing blurred teaser), **explicit refund SLA**, **restored SEBI + named-wins trust signals**, **single CTA with honest "free" framing**. Predicted median lift: **+4.6pt weighted** over V4 (48.6% vs 44%). Three operational preconditions must be met before ship (Section 4). Adversary flagged 3 blockers — none caused element revisions, all require ops/legal/product commitment. Confidence: **medium**; low tier is wide due to small-sample baselines (n=10-15 per segment in the source simulation).

---

## 1. Changes from V4 (the diff)

### 1.1 `trade_evidence` — V4 `blurred_card` → V5 `real_closed_trade`

- **What changes:** Replace the blurred/redacted trade card with a fully disclosed real closed trade. Stock name, entry price, exit price, days held, absolute rupee gain — all visible. No blur, no "unlock to see."
- **Replaces component:** `BlurredTradeCard` (semantic name; match Univest's actual component).
- **New component:** [`ClosedTradeCard`](#21-closedtradecard) — see spec in §2.
- **Citation:** `friction_points.blurred_card_alienates_skeptics` — *"Blurred trade card reads as a gimmick to Skeptical Investors. 12/12 (100% of segment). Persistent across V2/V3/V4."* Supporting quote: *"Show me a real trade or don't."*
- **Expected per-segment impact:** Skeptical +4 to +11pt (coupled-mechanism-adjusted). Other segments: neutral to small positive.
- **Untested:** yes. Mechanism is strong but operational preconditions (§4) must hold.

### 1.2 `refund_or_guarantee_copy` — V4 `absent` → V5 `explicit_sla`

- **What changes:** Add an explicit refund SLA line near the primary CTA. Must be operationally backed.
- **Replaces component:** none (V4 has no refund copy per source; see flag in §9).
- **New component:** [`RefundSlaLine`](#22-refundslaline) — see spec in §2.
- **Citation:** element-level source note — *"64% cited refund clause as strongest pricing reassurance."* Overlay mechanism: explicit SLA closes Skeptical trust gap.
- **Expected per-segment impact:** Skeptical +2 to +5pt. Cross-segment +1 to +2pt.
- **Untested:** yes. Adversary blocker 2 — SLA text must match operational reality.

### 1.3 `trust_signal` — V4 `implicit` → V5 `regulatory_plus_evidence` (sebi)

- **What changes:** Restore the SEBI registration number and named-wins carousel that V1 had and V2/V3/V4 dropped.
- **Replaces component:** V4 has no trust badge element.
- **New components:** [`RegulatoryBadge`](#23-regulatorybadge) + [`PastWinsCarousel`](#24-pastwinscarousel).
- **Citation:** V1 observational performance (Trust Seeker 60%, Curious Beginner 27%). `friction_points.abstract_metrics_vs_named_wins` — *"Abstract performance claims fail where named past wins (V1) succeeded. 8/50 (16%) cross-segment."*
- **Expected per-segment impact:** Trust Seeker +3 to +8pt. Curious Beginner +3 to +8pt.
- **Untested:** no (observed in V1, though confounded with evidence_detail).

### 1.4 `evidence_detail` — V4 `none` → V5 `named_past_outcome` (stock_named_with_rupee_gain)

- **What changes:** Previously-rendered carousel now names specific stocks with specific rupee gains. Paired with trust_signal block above.
- **Delivered via:** [`PastWinsCarousel`](#24-pastwinscarousel) — see §2.
- **Citation:** *"71% of V1 users cited a stock by name."* Curious Beginner anchor quote: *"I bought it last year — if they nailed that, I should listen."*
- **Untested:** no (observed in V1, confounded with trust_signal).

### 1.5 `cta_primary_label` — V4 `"Unlock FREE trade"` → V5 `"See 1 real trade, free"`

- **What changes:** Honest framing matching what the flow actually delivers. REQUIRES the subsequent flow to actually show the trade without payment friction (see Operational Precondition 1).
- **Replaces component:** `ActivationCTAButton` label prop.
- **Citation:** Overlay mechanism. V4 evidence: *"33% of V4 users noticed the discrepancy. 5/50 (10%) flagged as 'mildly deceptive.'"*
- **Expected per-segment impact:** Skeptical +1 to +3pt (removes trust erosion).
- **Untested:** yes. Adversary blocker 1 — legal review required + flow alignment.

### 1.6 `cta_stack` — V4 `dual_outline_plus_sticky` → V5 `single`

- **What changes:** Remove V4's outline "Unlock FREE trade" + sticky "₹1 Trial" pair. Replace with one primary CTA ([`ActivationCTA`](#25-activationcta)).
- **Replaces component:** `DualCtaStack`.
- **Citation:** `friction_points.dual_cta_label_mismatch` — 5/50 (10%) flagged the label mismatch; element-level 33% noticed the discrepancy.
- **Expected per-segment impact:** Cross-segment +0 to +2pt.
- **Untested:** no (single was V3's stack and performed well there).

### Unchanged from V4

`layout=full_screen`, `modal_interrupt=no`, `branding=none`, `price_visibility=visible_primary`, `cta_style=high_contrast_green`, `urgency_mechanism=none`.

> **Adversary obj-005** recommends A/B testing V5a (green) vs V5b (muted dark-teal) at ship. See §7.

---

## 2. Component specifications

### 2.1 `ClosedTradeCard`

**Purpose:** Show one fully disclosed recent closed winning trade to deliver on the "See 1 real trade, free" CTA promise and remove the blurred-card trust gap.

**Fields / props:**

| Name | Type | Source | Example |
|---|---|---|---|
| `stock_name` | string | `/api/v1/trades/closed` → latest | `"ZOMATO"` |
| `stock_ticker` | string | `/api/v1/trades/closed` → latest | `"ZOMATO"` |
| `entry_price` | decimal (₹) | `/api/v1/trades/closed` → latest | `142.50` |
| `exit_price` | decimal (₹) | `/api/v1/trades/closed` → latest | `165.85` |
| `days_held` | integer | `/api/v1/trades/closed` → latest | `3` |
| `rupee_gain` | decimal (₹) | computed: `(exit-entry) × qty` | `23435` |
| `trade_closed_at` | timestamp | `/api/v1/trades/closed` → latest | `2026-04-22T14:32Z` |
| `advisor_name` | string (optional) | `/api/v1/trades/closed` → latest | `"Rahul K."` |

**Copy strings (verbatim):**

- Card header: `"Closed trade — <days_held> days ago"`
- Outcome line: `"<stock_name> +₹<rupee_gain> in <days_held> day<s>"` (singular/plural on days)
- Entry/exit row: `"Entry ₹<entry_price> → Exit ₹<exit_price>"`
- Regulatory disclaimer (legally required): `"Past performance does not indicate future returns. This is one closed trade; not all trades are profitable."`
- Link: `"Browse all recent trades (mixed outcomes)"` — linked to full trade log. **Mandatory** per adversary obj-003 cherry-picking mitigation.

**Data contract:**

```
GET /api/v1/trades/closed?limit=1&sort=recency&filter=outcome:win&max_age_hours=24

Returns: { trade: ClosedTrade, has_recent_losses_in_pool: boolean }

Staleness rule: trade_closed_at must be within 24h. If no winning trade within 24h, fallback.
Fallback: render "Most recent trades are still open. Browse the last 30 days" with link to trade history. Do NOT render a stale card (> 24h old).
```

**Acceptance criteria:**

- [ ] Renders one winning closed trade with all six fields populated; zero-state if no trade < 24h old.
- [ ] "Browse all recent trades (mixed outcomes)" link is always visible when card renders.
- [ ] SEBI disclaimer visible at 12pt minimum on all viewports.
- [ ] If `has_recent_losses_in_pool=true`, card still renders (does not hide the loss context).
- [ ] Falls back gracefully (see staleness rule); never shows a card > 24h old.

### 2.2 `RefundSlaLine`

**Purpose:** Close Skeptical Investor's refund-disbelief gap with an explicit, operationally-backed SLA.

**Fields / props:**

| Name | Type | Source | Example |
|---|---|---|---|
| `payment_method` | enum: `upi` \| `card` \| `bank` | user's selected payment method at CTA | `"upi"` |
| `sla_text` | string | derived per payment_method (see copy) | — |

**Copy strings (verbatim, conditional on payment_method):**

- UPI: `"Refund in 2 minutes to UPI. No questions."`
- Card: `"Refund in 3–5 business days to card. No questions."`
- Bank: `"Refund in 1–3 business days. No questions."`
- Fallback (if method unknown at render time): `"Full refund to source. No questions asked."`

> **Deliberate revision from synthesize's "Refund in 60s to source":** adversary obj-002 flagged the 60s SLA as operationally unachievable for cards/bank. Revised copy matches actual payment-rail capability. Mechanism (explicit SLA → Skeptical trust closure) preserved; fiction removed.

**Data contract:** none — purely rendered copy based on payment method selection.

**Acceptance criteria:**

- [ ] Text updates reactively when user changes payment method.
- [ ] "No questions" language matches client's actual refund policy (Operational Precondition 2).
- [ ] Placement: directly below `ActivationCTA`, within 16px.

### 2.3 `RegulatoryBadge`

**Purpose:** Display SEBI registration number. Table-stakes compliance signal for Trust Seeker segment.

**Fields / props:**

| Name | Type | Source | Example |
|---|---|---|---|
| `sebi_number` | string | env var / settings | `"INA000016527"` |
| `label_prefix` | string | constant | `"SEBI Registered Advisor"` |

**Copy strings:**

- Full text: `"SEBI Registered Advisor: <sebi_number>"`

**Data contract:** reads `SEBI_REGISTRATION_NUMBER` from app config. Never hardcoded.

**Acceptance criteria:**

- [ ] Rendered in header area, visible above the fold on all viewports ≥ 320px wide.
- [ ] Font size ≥ 12pt, legible contrast ratio ≥ 4.5:1 against background.
- [ ] Clickable to a `/regulatory` page with full compliance info (not in V5 scope but link must exist).

### 2.4 `PastWinsCarousel`

**Purpose:** Anchor the Curious Beginner segment via named past stock wins. Replaces V2/V3/V4's missing evidence signal.

**Fields / props:**

| Name | Type | Source | Example |
|---|---|---|---|
| `wins` | array of `{ticker, pct_gain, days_held, trade_closed_at}` | `/api/v1/trades/top_recent_wins?limit=5&max_age_days=7` | see below |
| `refresh_interval_seconds` | integer | constant | `5` (for carousel rotation) |

Example `wins[0]`: `{ticker: "ZOMATO", pct_gain: 16.4, days_held: 3, trade_closed_at: "2026-04-20T..."}`

**Copy strings (per-card, templated):**

- `"<ticker> +<pct_gain>% in <days_held> day<s>"`

**Data contract:**

```
GET /api/v1/trades/top_recent_wins?limit=5&max_age_days=7

Returns: { wins: WinItem[], total_closed_trades_in_period: integer, win_rate: decimal }

Staleness rule: every win.trade_closed_at ≤ 7 days old.
Fallback: if fewer than 3 wins in last 7 days, do NOT render a reduced carousel — hide the component entirely and do not claim a carousel track record.
```

**Acceptance criteria:**

- [ ] Component hides itself if the API returns < 3 wins in 7 days. No misleading "best performing" claim on a thin track record.
- [ ] Each card is tappable and navigates to that trade's full disclosure (same view as `ClosedTradeCard` §2.1 for that stock).
- [ ] Carousel pauses on tap, resumes after 10s idle.
- [ ] Regulatory disclaimer visible near carousel (see `RegulatoryBadge` — may be unified).

### 2.5 `ActivationCTA`

**Purpose:** The one primary CTA. Replaces V4's dual stack.

**Fields / props:**

| Name | Type | Source | Example |
|---|---|---|---|
| `label` | string | constant (see Copy §3) | `"See 1 real trade, free"` |
| `cta_style` | enum: `high_contrast_green` \| `muted_premium` | A/B test flag | `"high_contrast_green"` |
| `onClick` | function | routes to trade-view flow | — |

**Copy strings:**

- Primary (V5a / green): `"See 1 real trade, free"`
- Alternative (V5b / muted_premium): same label, different style

**Data contract:** no data fetch; pure UI.

**Acceptance criteria:**

- [ ] Tapping the CTA navigates to the trade-view flow that shows the ClosedTradeCard **without any payment step** (Operational Precondition 1). This is the "free" promise delivered.
- [ ] Sticky: remains visible at bottom of viewport on scroll.
- [ ] Minimum tap target 44×44 pt.
- [ ] Style variant selectable via feature flag (`cta_style_variant`) for V5a/V5b A/B test (Section 7).
- [ ] Text rendered verbatim, no A/B on the label string itself.

---

## 3. Copy book

| Key | Text | Length | Reviewer gate |
|---|---|---|---|
| `activation.cta.primary` | `"See 1 real trade, free"` | 23 chars | **legal** — adversary obj-001, word "free" flagged |
| `activation.refund_sla.upi` | `"Refund in 2 minutes to UPI. No questions."` | 42 | **ops** — must match actual SLA capability |
| `activation.refund_sla.card` | `"Refund in 3–5 business days to card. No questions."` | 51 | **ops** |
| `activation.refund_sla.bank` | `"Refund in 1–3 business days. No questions."` | 43 | **ops** |
| `activation.regulatory.badge` | `"SEBI Registered Advisor: <sebi_number>"` | ~40 | — (regulated copy; do not modify) |
| `trade_card.header` | `"Closed trade — <days_held> days ago"` | — | — |
| `trade_card.outcome` | `"<ticker> +₹<rupee_gain> in <days> day(s)"` | — | — |
| `trade_card.disclaimer` | `"Past performance does not indicate future returns. This is one closed trade; not all trades are profitable."` | 121 | **legal** — SEBI past-performance rule |
| `trade_card.browse_link` | `"Browse all recent trades (mixed outcomes)"` | 42 | — |
| `carousel.card_template` | `"<ticker> +<pct_gain>% in <days> day(s)"` | — | — |

---

## 4. Operational preconditions (hard prerequisites)

From [adversary_review.json](./adversary_review.json) blockers. **If any of these cannot be committed before ship, descope V5 to V5-narrow (keep only `PastWinsCarousel` + `RegulatoryBadge`; revert the three untested changes).**

- [ ] **Precondition 1: "Free" means free.** The `ActivationCTA` label `"See 1 real trade, free"` must navigate to a flow that shows the closed trade card WITHOUT any payment step. The ₹1 subscription step must come AFTER the trade is shown (or never — if the user can browse one trade for free and subscribe only for ongoing advice). Owner: Product. Measurable: funnel analytics show ≤ 2% drop-off at any step labeled "₹1" before the trade view renders.

- [ ] **Precondition 2: Refund SLA matches payment-rail reality.** Revised per-method SLA copy (§2.2) must match Univest's operational p90 refund time per method, measured on actual historical refunds. Owner: Ops + Finance. Measurable: ops sign-off document comparing stated SLA to p90 actuals.

- [ ] **Precondition 3: Real trade card operational rules.**
  - Source: `/api/v1/trades/closed` returns the most recent closed WINNING trade, max 24h old. Owner: Backend.
  - Cherry-picking mitigation: `"Browse all recent trades (mixed outcomes)"` link always present and functional. Owner: Frontend + Backend.
  - SEBI past-performance disclaimer: legally reviewed copy visible. Owner: Legal.
  - Fallback: if no winning trade in 24h, card hides (not replaced with stale card). Owner: Frontend.
  - Measurable: pre-ship test renders V5 at every hour of a representative week; card shows fresh real trade OR hides; never shows stale.

- [ ] **Precondition 4 (from adversary obj-002 adverse-selection concern):** Track V5 cohort 30-day LTV. If cohort LTV ≥ 20% below V4 cohort despite higher activation, suspend V5 rollout. Owner: Product analytics. Not a pre-ship gate; post-ship kill-switch.

---

## 5. Instrumentation

Every kill-condition from [conversion_estimates.json](./conversion_estimates.json) becomes an observation-layer event.

| Event name | Trigger | Properties | Kill threshold |
|---|---|---|---|
| `v5_activation_impression` | `ActivationScreen` rendered | `cta_style_variant`, `segment_inferred`, `viewport_height` | — baseline |
| `v5_closed_trade_card_rendered` | `ClosedTradeCard` appears | `stock_name`, `trade_age_hours`, `is_win`, `had_loss_in_pool` | **Kill Skeptical** if `trade_age_hours > 24` rate > 5% |
| `v5_closed_trade_card_hidden` | fallback fired | `reason` (`no_recent_win`, `api_error`) | **Kill Skeptical** if hidden rate > 20% |
| `v5_free_cta_clicked` | user taps `ActivationCTA` | `segment_inferred`, `cta_style_variant` | — |
| `v5_trade_shown_before_payment` | trade view rendered pre-payment | (binary) | **Kill obj-001** if this event never fires — means flow broke the "free" promise |
| `v5_payment_required_before_trade` | ₹1 step shown before trade | — | **Kill obj-001 immediately** — stop-ship |
| `v5_refund_issued` | refund completed | `payment_method`, `elapsed_seconds` | **Kill Precondition 2** if p90 elapsed_seconds > stated SLA for ≥ 1 week |
| `v5_carousel_engagement` | time on `PastWinsCarousel` | `seconds`, `taps`, `segment_inferred` | **Kill Curious** if Curious avg `seconds` < 2 |
| `v5_conversion` | ₹1 subscription started | `segment_inferred`, `cta_style_variant`, `time_to_convert_seconds` | **Kill Bargain** if `time_to_convert_seconds` p50 > 10s |
| `v5_cohort_ltv_30d` | 30 days post-activation | cohort-level | **Kill Precondition 4** if cohort LTV ≥ 20% below V4 |

---

## 6. Predicted conversion

From [conversion_estimates.json](./conversion_estimates.json). Wilson 95% intervals + coupled-mechanism discount for Skeptical.

| Segment | n | V4 actual | V5 low | V5 point | V5 high | Primary kill-condition |
|---|---|---|---|---|---|---|
| Skeptical Investor | 12 | 25% | **9%** | **32%** | **36%** | Skeptical conv ≤ 27% after 2 weeks (mechanisms not transferring) |
| Curious Beginner | 15 | 33% | **15%** | **40%** | **44%** | Carousel engagement < 2s avg (anchor didn't land) |
| Bargain Hunter | 13 | 69% | **42%** | **71%** | **73%** | Time-to-convert p50 > 10s (cognitive load) |
| Trust Seeker | 10 | 50% | **24%** | **52%** | **56%** | V5 Trust < 47% (green penalty bigger than measured — switch to muted_premium) |
| **Weighted overall** | — | **44%** | **22.3%** | **48.6%** | **52.0%** | — |

> **Why the low tier is wide:** baseline Wilson CIs on n=10-15 per segment are inherently wide. V4's 25% Skeptical conversion has a 95% CI of [9%, 53%] — V4's "true" Skeptical rate was never precisely 25%, it was somewhere in that band. V5's lift is layered on top, so the low tier inherits the baseline uncertainty. This is not a prediction that V5 will fail; it's the honest information content of a 5-variant test at n=50.

---

## 7. Rollout recommendation

**Ramp schedule:**
- Week 1: 10% of activation traffic on V5, 90% on V4 (holdout).
- Week 2: 50/50 split, enable kill-switches against Section 5 events.
- Week 3: 100% V5 if no kill-condition tripped AND no Preconditions-4 alarm.

**A/B alternatives to run:**
- V5a: `cta_style=high_contrast_green` (primary; +6.42pt observed).
- V5b: `cta_style=muted_premium` (adversary obj-005 hedge against wider-than-measured green penalty on Trust Seeker).
- 50/50 split within V5 traffic. Decide primary based on 2-week cumulative Trust Seeker conversion delta.

**Stop-ship criteria (immediate rollback):**
- `v5_payment_required_before_trade` fires at all (Precondition 1 broke).
- `v5_closed_trade_card_hidden` rate > 20% for 24h.
- Legal retracts approval on "free" language or SEBI disclaimer.
- Any segment conversion underperforms V4 by > 5pt over 2 weeks.

---

## 8. What this spec deliberately does NOT prescribe

The simulation's 5 variants produced limited evidence for these dimensions. V5 keeps V4's values; any change here requires a separate test.

- **`layout`**: V5 uses `full_screen` (V4's choice). No clean contrast vs `full_screen_dark`. If Univest wants to test dark theme, it requires a separate V6.
- **`branding`**: V5 uses `none` (V4's choice). Only a weak `default_by_adoption_rate` citation supports this. Adversary obj-004 recommends a quick V5a (none) vs V5b (logo_only) test before full ship on Trust-heavy audiences.
- **`cta_primary_label`** was a change, but the exact wording `"See 1 real trade, free"` is one defensible candidate; others ("See a real closed trade, free", "Free: see one real trade") are within the mechanism envelope. Copywriting team has latitude.
- **Stock selection for `PastWinsCarousel`**: the carousel's effect depends on which stocks are named (adversary obj-006). Spec leaves this to product analytics — default is `GET /api/v1/trades/top_recent_wins?limit=5&max_age_days=7`, but personalization to user's watchlist is an untested upgrade.

---

## 9. Cross-references and caveats

- [synthesized_variant.md](./synthesized_variant.md) — narrative V4 vs V5 for PM review.
- [adversary_review.json](./adversary_review.json) — full structured objections (blockers + should-fix + instrument).
- [conversion_estimates.json](./conversion_estimates.json) — Wilson intervals, coupling discount math, per-segment kill-conditions.
- [element_matrix.json](./element_matrix.json) — the 5-variant simulation raw evidence.

**Caveats:**

1. The source simulation ([apriori.work/demo/univest](https://apriori.work/demo/univest)) tags `V4.refund_or_guarantee_copy=absent`, but a V4 Skeptical quote mentions refund. **If V4 actually shipped with refund copy**, V5's change in §1.2 is a known-safe upgrade to existing copy (lower risk); if it didn't, §1.2 is a new element and carries the full untested risk. Recommend visual verification of V4's live UI before ship. (`element_matrix.flags` item 2.)

2. Segment weights (Skeptical 24%, Curious 30%, Bargain 26%, Trust 20%) come from the simulation's persona composition. If Univest's actual user base differs, re-run `weigh-segments` + `synthesize` with override weights.

3. **Confidence is medium**, not high. The binding constraint is sample size in the source simulation (n=10-15 per segment). Future simulations should target n ≥ 30 per segment to narrow the Wilson bands to usable widths.

---

*Spec generated by the Multiverse Synthesis Engine. V1 of the engine, V5 of the Univest activation screen.*

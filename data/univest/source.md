# Apriori simulation — Univest ₹1 trial activation

**Source:** https://apriori.work/demo/univest
**Extracted:** 2026-04-23
**N:** 50 synthetic personas
**Variants tested:** 5 (Control, V1, V2, V3, V4)

This file is the immutable source of truth for the parse-simulation skill. Edits here invalidate every downstream artifact. If the upstream page changes, re-fetch into `data/univest/source-v2.md` (sibling in this folder, same naming pattern every client uses) rather than overwriting this file.

---

## 1. Variants

### Control
- Layout: bottom-modal popup
- CTA: "Start Trial Now"
- Price visibility: **no ₹1 visible on screen**
- Background: greyed-out Live Trades screen behind modal

### Variant 1 (V1)
- Layout: full-screen dark theme
- Trust signal: SEBI number prominent; Recent Wins carousel naming stocks (TMPV, ZOMATO, RELIANCE)
- Price visibility: explicit ₹1 sticky CTA
- Urgency: **countdown timer "04:34 Left"**
- Trade evidence: named past wins (carousel)

### Variant 2 (V2)
- Layout: full-screen
- Branding: crown header
- Price visibility: ₹1 + refund banner ("Activate @ ₹1 & get instant refund")
- Trade evidence: blurred trade card
- CTA: low-contrast (visually subordinate to banner)

### Variant 3 (V3)
- Layout: full-screen, crown header (same as V2)
- Single change vs V2: **CTA is high-contrast green**
- Trade evidence: blurred trade card (retained from V2)
- Price visibility: ₹1 + refund banner (retained)

### Variant 4 (V4)
- Layout: full-screen
- CTA stack: **dual CTA** — outline "Unlock FREE trade" + sticky green "₹1 Trial"
- Trade evidence: blurred trade card
- Urgency: **no countdown timer**
- Price visibility: ₹1 sticky

---

## 2. Audience segments

| Segment | n | % of 50 |
|---|---|---|
| Skeptical Investor | 12 | 24% |
| Curious Beginner | 15 | 30% |
| Bargain Hunter | 13 | 26% |
| Trust Seeker | 10 | 20% |

---

## 3. Conversion rates (segment × variant)

| Segment | Control | V1 | V2 | V3 | V4 | Winner |
|---|---|---|---|---|---|---|
| Skeptical Investor (n=12) | 8% | 17% | 8% | 17% | 25% | V4 |
| Curious Beginner (n=15) | 7% | 27% | 20% | 27% | 33% | V4 |
| Bargain Hunter (n=13) | 38% | 54% | 46% | 62% | 69% | V4 |
| Trust Seeker (n=10) | 40% | 60% | 50% | 40% | 50% | V1 |

Overall (weighted by audience composition):
- V4: **44%** (headline result)

---

## 4. Friction points

### Resolved (Control → V1-V4)
- Price opacity: 39/50 users. Fixed in V1-V4 by making ₹1 visible.
- Modal interrupts: 31/50 users. Fixed in V1-V4 by full-screen layout.

### Introduced (specific variants)
- **Countdown timer manipulation:** 6/50 users. V1 only.
- **Dual CTA label mismatch:** 5/50 users. V4 only. (33% of V4 users noticed the discrepancy per element-level note.)
- **Green CTA reduces premium feel:** 4/50 users. V3 only.

### Persistent (unfixed across V2/V3/V4)
- **Blurred trade card alienates Skeptical Investors:** 12/50 users (V2/V3/V4).
- **Abstract metrics vs. concrete past wins:** 8/50 users (V2/V3/V4).

---

## 5. Persona quotes

### Skeptical Investor (n=12)
- "Trial without a price means hidden charge" — Control reaction.
- "Show me a real trade or don't" — V2/V3 blurred card reaction.
- "I still don't believe the 84.7% claim, but ₹1 with a refund is essentially free" — V4.

### Curious Beginner (n=15)
- "I bought it last year — if they nailed that, I should listen" — V1 ZOMATO win.

### Trust Seeker (n=48)
> NB: source page shows "Trust Seeker (n=48)" here; elsewhere Trust Seeker segment is n=10 of 50. The 48 likely refers to cross-segment aggregate respondents on this specific quote, not the segment size. Flagged for verification.
- "Best of both worlds — looks premium and tells me the price" — V4.

---

## 6. Aggregate metrics

| Metric | Control | V1 | V2 | V3 | V4 | Best |
|---|---|---|---|---|---|---|
| Completion Rate | 22% | 38% (+16) | 30% (+8) | 36% (+14) | 44% (+22) | V4 |
| SUS Score | 58.4 (C) | 68.7 (B, +10.3) | 64.2 (C, +5.8) | 70.4 (B, +12) | 73.6 (B, +15.2) | V4 |
| SEQ Score | 3.2 | 4.6 (+1.4) | 4.1 (+0.9) | 4.9 (+1.7) | 5.2 (+2.0) | V4 |
| Avg Sentiment | −0.32 | 0.08 (+0.4) | −0.04 (+0.3) | 0.18 (+0.5) | 0.32 (+0.6) | V4 |
| Friction Points | 3 | 2 | 3 | 3 | 3 | V1 |

---

## 7. Element-level notes (from source)

- Recent Wins (V1): 71% cited a stock by name.
- Refund clause: 64% cited as strongest pricing reassurance.
- V1 Bargain Hunter conversion took avg 11s; V4 Bargain Hunter took avg 7s.
- V2 CTA visibility: 22% of users missed the CTA entirely or tapped the banner by mistake.
- V4 dual-CTA discrepancy: 33% of users noticed the mismatch.
- V3 Trust Seeker penalty: conversion dropped from 50% (V2) to 40% due to green CTA tone shift.

---

## 8. Known unknowns / flags

- Trust Seeker n inconsistency: segment size is 10, but one quote is attributed to "n=48." Treat as aggregate, not segment-bound.
- SUS letter grades (C, B) shown alongside numbers — kept verbatim.
- Exact conversion rates are rounded percentages, not raw counts. Small-sample uncertainty not represented here.

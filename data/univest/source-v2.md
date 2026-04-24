# Apriori simulation — Univest ₹1 trial activation (CORRECTED RE-EXTRACTION)

**Source:** https://apriori.work/demo/univest
**Re-extracted:** 2026-04-24
**Supersedes:** [`source.md`](source.md) — kept for audit trail per source-immutability rule.
**N:** 50 synthetic personas
**Variants tested:** 5 (Control, V1, V2, V3, V4)

This file is the corrected extraction. The original `source.md` (2026-04-23) was extracted from the source page's *text descriptions only* and missed multiple visual elements present in the actual variant screenshots. The screenshots are now saved as immutable artifacts at `source-screenshots/{control,v1,v2,v3,v4}.png`.

---

## What changed from `source.md` (the corrections)

The original extraction was based on the source page's prose variant descriptions. Those descriptions are incomplete — they highlight the variant-distinguishing elements but omit shared elements that carry over across V1-V4. Below are the elements present in the screenshots that `source.md` did not capture.

### Critical corrections

1. **Trial offer is "3 FREE Trades" not "1"** (or "3 Stock/F&O Ideas" on Control). Visible in the prominent banner across all variants. The original extraction inferred singular from V4's "Unlock FREE trade" CTA and the source page's prescriptive recommendation ("show one real trade") — but the actual offer the user sees is THREE.

2. **V1 shows a wins/losses ratio**: "All-time accuracy 84.7% (914 wins · 62 losses)." This is V1's structural defense against cherry-picking — the user sees that the 84.7% claim is backed by a full denominator including 62 losses. The original extraction missed this entirely; it was the highest-leverage trust signal in V1 that V5 should adopt.

3. **V4 has a countdown timer** ("04:34 Left"). The original extraction said `urgency_mechanism=none` for V4 because the source page's prose said "no countdown timer." The screenshot shows it's still there, just in the upper-right of the refund banner.

4. **V4 has "Activate @ ₹1 & Get instant refund" banner.** The original extraction said `refund_or_guarantee_copy=absent` for V4. The banner is plainly visible in V4's screenshot, identical to V2/V3's banner.

5. **V4 has crown branding.** The original extraction said `branding=none` for V4. The crown icon at the top of V4 matches V2/V3.

6. **Control has rich trust signals**: "By SEBI Reg. RA - INH000013776", "Google for Startups Accelerator 2024", "Awarded No.1 by Economic times", "Trusted by 50 lakh+ Indians", 5-star rating, "2300+ Profitable Ideas", "84.7% Accuracy." The original extraction said `trust_signal=implicit` for Control — clearly wrong.

7. **V2-V4 have aggregate-metric trust signals** ("SEBI Reg. Research Advisors", "85%+ Accuracy Rate", "3500+ Profitable Trades"). These weren't captured. V1 has the same plus the named-wins carousel and the wins/losses ratio.

### Why these were missed

The original extraction relied on the source page's variant prose, which is *prescriptive* (what differentiates each variant) not *descriptive* (what's on the screen). Screenshots are required for accurate extraction. Lesson logged.

---

## 1. Variants (corrected)

### Control (`source-screenshots/control.png`)
- **Layout:** bottom-modal popup (white card sliding up over a greyed-out Live Trades app screen)
- **Background:** Live Trades app visible behind modal — "Buy PRO" CTA, ratings, bottom nav all visible (creates the "interrupting" feeling)
- **Modal headline:** "3 STOCK/F&O IDEAS FOR FREE" (large, in red)
- **Header text in modal:** "2300+ Profitable Ideas · 84.7% Accuracy"
- **Sub-headline:** "By SEBI Reg. RA - INH000013776"
- **Trust signals:** Google for Startups Accelerator 2024 logo, "Awarded No.1 by Economic times" with ET logo, 5-star rating with "Trusted by 50 lakh+ Indians"
- **CTA:** "Start Trial Now" (dark/black sticky button at bottom of modal)
- **Refund/cancel:** "Cancel anytime" subtext below CTA
- **Price:** **NOT shown on the modal** (no ₹1 visible in the modal CTA or banner)
- **Urgency:** none

### Variant 1 (`source-screenshots/v1.png`)
- **Layout:** full-screen dark theme (navy / very dark blue background)
- **Header:** "India's Trusted Advisory" + "SEBI INH000013776" (registration number explicit and prominent)
- **Trust display:** "All-time-accuracy **84.7%**" with "(**914 wins · 62 losses**)" — wins+losses ratio prominently shown
- **Banner:** "Claim your **3 FREE Trades**" + "Stocks | Futures | Options"
- **Urgency:** "**04:34 Left**" countdown timer in the banner
- **Recent Wins carousel** (closed trades, named): 
  - TMPV +12.93% Net Gain "Closed same day" (with fire emoji)
  - ZOMATO ₹23,435 Net Gain "Closed in 3 days"
  - RELIANCE +12.93% (truncated, partial visibility)
- **LIVE Trades section** (live, distinct from Recent Wins):
  - Two cards visible, both labeled "Short term" with "Potential Gain"
  - Card 1: "Potential Gain +16.2%" with "Open FREE" button
  - Card 2: "Potential Gain ₹1,23,343" with "Open FREE" button
  - Stock names NOT shown in Live Trades section (these are gated)
- **Customer feedback** section header visible at bottom
- **Sticky bottom CTA:** "**START FREE TRIAL @ ₹1 →**" (dark/black button)
- **Branding:** none (no crown)

### Variant 2 (`source-screenshots/v2.png`)
- **Layout:** full-screen, white/light background
- **Branding:** **crown header** (small blue crown icon centered at top)
- **Header:** "India's Trusted Advisory · Stocks · F&O · Commodity"
- **Trust display row:** "SEBI Reg. Research Advisors" + "**85%+ Accuracy Rate**" + "**3500+ Profitable Trades**" (three columns, aggregate metrics)
- **Banner (dark blue):** "Claim 3 FREE Trades →" / "Activate @ ₹1 & Get instant refund" + "**04:34 Left**" countdown
- **LIVE TRADES section:**
  - Card visible with "Stock trade" tag, "Active" indicator
  - "POTENTIAL GAINS +14.32%" prominent
  - Stock name, entry price, target price columns — **all blurred** (this is the "blurred trade card" friction)
- **CTA:** "**Unlock FREE trade →**" (dark/black single button, low contrast vs the blue banner above it)
- **Second card peeking** at bottom (also "Stock trade", "Active")

### Variant 3 (`source-screenshots/v3.png`)
- **Identical to V2** in every respect EXCEPT:
- **CTA color:** "Unlock FREE trade →" is now **bright green** (high_contrast_green), not dark
- All other elements (crown, banner, trust row, blurred card) carry over from V2

### Variant 4 (`source-screenshots/v4.png`)
- **Identical to V3 base** in: dark theme switched to dark again (V4 reverts to dark theme!) — note this is V4's screenshot which appears DARK like V1, not white like V2/V3. **WAIT — re-checking: V4 has DARK background** (different from V2/V3). Crown still present. Banner present. Countdown present. Live Trades section present.
- **Header:** "India's Trusted Advisory" + "Stocks · F&O · Commodity"
- **Trust display row:** "SEBI Reg. Research Advisors" + "85%+ Accuracy Rate" + "3500+ Profitable Trades"
- **Banner:** "Claim 3 FREE Trades →" / "Activate @ ₹1 & Get instant refund" + "**04:34 Left**" countdown
- **LIVE TRADES section:** Stock card with "POTENTIAL GAINS +14.32%", stock name/entry/target blurred
- **Outline CTA (mid-screen):** "**🔒 Unlock FREE trade →**" (outline-style, green border, no fill)
- **Sticky bottom CTA:** "**Start FREE Trial @ ₹1 →**" (solid green, sticky)
- **CTA stack:** dual — outline + sticky
- **Branding:** crown (carries from V2/V3)

NB on V4 background — the screenshot is dark-themed. This means V4 reverted to V1's dark theme aesthetic while keeping V2/V3's crown + banner + blurred-card layout. Our original matrix had V4 as `layout=full_screen` (light); the actual layout is `full_screen_dark`. This is another correction.

---

## 2. Audience segments (unchanged)

| Segment | n | % of 50 |
|---|---|---|
| Skeptical Investor | 12 | 24% |
| Curious Beginner | 15 | 30% |
| Bargain Hunter | 13 | 26% |
| Trust Seeker | 10 | 20% |

---

## 3. Conversion rates (unchanged from source.md)

| Segment | Control | V1 | V2 | V3 | V4 | Winner |
|---|---|---|---|---|---|---|
| Skeptical Investor (n=12) | 8% | 17% | 8% | 17% | 25% | V4 |
| Curious Beginner (n=15) | 7% | 27% | 20% | 27% | 33% | V4 |
| Bargain Hunter (n=13) | 38% | 54% | 46% | 62% | 69% | V4 |
| Trust Seeker (n=10) | 40% | 60% | 50% | 40% | 50% | V1 |

Overall (weighted by audience composition):
- V4: **44%** (headline result)

---

## 4. Friction points (unchanged from source.md, screenshot-validated)

The friction findings from `source.md` are validated by the screenshots:
- "Blurred trade card alienates Skeptical Investors" — visible in V2/V3/V4 stock-name/entry/target blur ✓
- "Countdown timer manipulation" — V1's "04:34 Left" timer visible ✓ (and persists in V2/V3/V4)
- "Dual CTA label mismatch" — V4's "Unlock FREE trade" outline + "Start FREE Trial @ ₹1" sticky visible ✓
- "Green CTA reduces premium feel" — V3's bright-green CTA visible ✓
- "Abstract metrics vs concrete past wins" — V2/V3/V4 show "85%+ / 3500+" aggregate; V1 shows named TMPV/ZOMATO/RELIANCE ✓

---

## 5. Persona quotes (unchanged from source.md)

See `source.md` Section 5. Quotes are unaffected by the visual extraction corrections.

---

## 6. Aggregate metrics (unchanged from source.md)

See `source.md` Section 6.

---

## 7. Element-level notes (unchanged from source.md)

See `source.md` Section 7.

---

## 8. Source-page prescriptive recommendation (verbatim from rendered demo)

The source page itself recommends:

> **Recommended: Variant 4 with modifications.**
>
> Variant 4 is the highest-converting screen in the study (44%) and the only design that meaningfully cracks the Skeptical Investor segment (25%, up from 8% in Control). The dual-CTA stack lets users self-segment into 'explore first' or 'commit now', and the sticky '₹1 Trial' button makes price impossible to miss.
>
> The recommended path is Variant 4's dual-CTA layout with the blurred trade card replaced by a real closed trade, and the outline 'Unlock FREE trade' CTA made functionally different from the ₹1 activation.
>
> **Modifications needed:**
> • Replace the blurred Live Trade card with a real closed trade showing entry, exit, days held, and rupee gain
> • Make the dual CTAs functionally different — let 'Unlock FREE trade' show one real trade for free, reserve ₹1 sticky CTA for full activation

The synthesis engine treats this as ONE input (the source's opinion), not as ground truth. Our V5 may agree or disagree with this prescription based on the data.

---

## 9. Known unknowns / flags (corrected)

- **Trial-count discrepancy in V4:** The big banner says "Claim 3 FREE Trades" but the outline CTA says "Unlock FREE trade" (singular). This is itself a copy inconsistency in V4 — possibly part of the dual-CTA-mismatch friction the source notes. V5 must resolve which framing to commit to.
- **Trust Seeker n inconsistency:** Same as `source.md`. Segment size is 10; one quote attributed to "n=48" treated as aggregate.
- **Conversion rates are rounded percentages**, not raw counts. Small-sample uncertainty not represented.
- **Live Trades section** is present in V1/V2/V3/V4 but the trades shown there are LIVE (potential gains, not closed). The Recent Wins carousel in V1 shows CLOSED past trades. These are two different UI elements; V2/V3/V4 dropped the Recent Wins carousel and retained only the Live Trades section (with stock names blurred to gate access).

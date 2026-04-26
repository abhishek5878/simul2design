# Element taxonomy — base (client-neutral)

The dimensions and values that apply to any activation / subscription / conversion-flow simulation, independent of domain. Every client's taxonomy inherits from this and extends it with domain-specific values in `.claude/rules/element-taxonomy-<client>.md`.

If a value you need doesn't exist here AND doesn't make sense in the base (because it only applies to one vertical), put it in the client overlay. If you find yourself wanting to add something that's also useful to a hypothetical second client in a different domain, it belongs in the base.

Version: 1.0.

## Base dimensions (must be present in every variant, any client)

### 1. `layout`
- `bottom_modal` — popup over a background view
- `full_screen` — dedicated activation/landing screen
- `full_screen_dark` — full-screen with dark theme
- `inline` — embedded in a larger page flow
- `side_panel` — slide-in drawer

### 2. `modal_interrupt`
- `yes` — modal or overlay over background
- `no` — dedicated surface

### 3. `branding`
- `none`
- `crown_header` — premium-style top banner with iconography
- `logo_only` — brand logo without premium styling

### 4. `price_visibility`
- `opaque` — no price shown on activation surface
- `visible_primary` — price visible on main CTA
- `visible_with_framing` — price visible plus additional framing copy (refund / trial / guarantee)

### 5. `cta_primary_label`
- Freeform string. The button text itself. Preserve verbatim. The synthesize/spec-writer skills treat this as natural language.

### 6. `cta_style`
- `neutral_default` — primary CTA, color unspecified / standard
- `low_contrast_subordinate` — low-contrast AND visually subordinate to another element
- `high_contrast_warm` — bright red/orange/yellow
- `high_contrast_cool` — bright blue/teal
- `high_contrast_green` — bright green (conversion-standard)
- `muted_premium` — dark teal / charcoal / muted — high visibility, premium tone
- `text_link` — underlined text, no button

### 7. `cta_stack`
- `single` — one primary CTA
- `dual_outline_plus_sticky` — outline button + sticky button
- `dual_side_by_side` — two equally-weighted buttons side-by-side
- `primary_plus_secondary_link` — primary button + text secondary

### 8. `urgency_mechanism`
- `none`
- `countdown_timer` — visible ticking timer
- `scarcity_count` — "only X seats left"
- `social_proof_realtime` — "N people viewing now"
- `deadline_text` — static end date

### 9. `refund_or_guarantee_copy`
- `absent`
- `implicit_refund` — generic "refund" mention, no SLA
- `explicit_sla` — specific SLA ("refund in 60s to source, no questions")
- `money_back_guarantee` — time-bounded guarantee
- `no_questions_asked` — permissive return framing

### 10. `trust_signal`
- `implicit` — no explicit trust markers
- `regulatory` — any regulator / authority number (SEBI, FCA, SEC, etc.) — specify which in the client overlay
- `third_party_endorsement` — press mentions, reviewer logos
- `evidence_mode` — concrete evidence (user count, named past outcomes, testimonials) — specify kind in the client overlay
- `regulatory_plus_evidence` — both above

### 11. `evidence_detail` (subordinate to `trust_signal=evidence_mode` or `=regulatory_plus_evidence`)
- `none`
- `aggregate_metric` — e.g., "84% accuracy"
- `named_past_outcome` — e.g., "ZOMATO +₹23,435"
- `user_testimonial` — individual quote
- `third_party_logos` — "As seen on..."
- `real_outcome_disclosure` — entry / exit / duration / gain fully disclosed

## Design decisions

- **`cta_primary_label` is freeform, not enumerated.** Label text matters to the synthesizer's natural-language reasoning, and the enumeration gets unwieldy fast. Preserve verbatim; let `synthesize` reason over it.
- **`trust_signal` and `evidence_detail` are separate dimensions.** First pass of this taxonomy bundled them into a single `trust_signal` enum; the split was applied after a spot-check observed that regulatory-presence and evidence-presence are independently variable in practice. Keep them separate.
- **Dimensions that vary by vertical (specific regulator names, specific evidence formats) resolve via the client overlay.** Base declares the *kind* of value; overlay declares the actual values seen in that client's data.

## How to extend for a new client

Create `.claude/rules/element-taxonomy-<client>.md` with:

1. A **Client context** section (one paragraph — domain, vertical, what the activation screen is for).
2. A **Domain-specific values** section listing any enumeration values not in the base (e.g., `regulatory=sebi`, `evidence_detail=named_past_outcome:stock_named` for India fintech).
3. A **Variant mapping table** — each variant × each base dimension, plus any overlay-only dimensions.
4. An **Extraction confidence** section for values that were inferred rather than directly extracted.
5. A **Contradictions** section (domain-specific conflict rules — e.g., "urgency_mechanism=countdown_timer alienates trust_signal=regulatory_plus_evidence audiences").

Do NOT modify this base file to fit a client. If a genuine generalization emerges (e.g., two clients both need a dimension we didn't have), lift it to the base here with a note about which client surfaced it.

## When to split a dimension

If a single dimension has allowed values that observably behave independently across segments (e.g., SEBI-number-present and named-wins-present have separable effects), split the dimension. Do NOT wait for the synthesizer to trip on it; split on the next spot-check if the evidence is already there.

## Open dimensions (being considered for base v1.1)

- `first_screen_friction` — captcha / email-gate / phone-gate present at activation.
- `social_proof_position` — above CTA / below CTA / absent.
- `pricing_anchor` — whether a higher price is shown and struck through.

Leave these in the overlay for the client that surfaces them until two clients independently need them.

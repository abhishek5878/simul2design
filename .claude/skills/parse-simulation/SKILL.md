---
name: parse-simulation
description: Trigger when the user provides simulation output (Apriori-style or similar) for any client to be ingested for prescriptive synthesis. Produces a normalized `data/<client>/element_matrix.json` that every downstream skill depends on. Client-agnostic by design — every client gets its own folder, its own source file, its own taxonomy overlay. Load-bearing — taxonomy errors here compound downstream.
---

# parse-simulation skill

**Client-agnostic.** This skill ingests simulation data for *any* client — fintech, SaaS, e-commerce, whichever. The workflow is identical; the client-specific detail lives entirely in the client folder and the client taxonomy overlay. Never hardcode client names, segment names, or domain-specific element values in this skill.

## When to use

- User provides a URL, file, or text blob of simulation results for a specific client.
- A re-fetch is needed because source data changed (creates a new suffixed source file, never overwrites).
- A new client's simulation needs to be ingested.

## When NOT to use

- User wants a variant synthesized (that's `synthesize`, requires this skill to have run first for that client).
- User wants to change the base taxonomy itself (edit `.claude/rules/element-taxonomy-base.md` directly, then re-run this).
- The simulation's matrix already exists in `data/<client>/element_matrix.json` and hasn't changed.

## Inputs required (ask if missing)

1. **Client slug** — short lowercase kebab-case (e.g., `univest`, `acme-saas`). Becomes the data folder name.
2. **Source** — URL, file path, or pasted text.
3. **Domain hint** (optional but useful) — `fintech-in`, `saas`, `ecomm`, etc. Tells the skill which (if any) existing taxonomy overlay to start from.

If any is missing, ask before fetching.

## Workflow

1. **Fetch or read the source.**
   - URL → WebFetch.
   - File → Read.
   - Pasted → accept as-is.
2. **Save raw to `data/<client>/source.md`.**
   - If the file already exists: do NOT overwrite. Create `data/<client>/source-v2.md` (or v3, etc.). Document why in the new file's header.
3. **Load or fork the taxonomy.**
   - Always load base: `.claude/rules/element-taxonomy-base.md`.
   - If `.claude/rules/element-taxonomy-<client>.md` exists, load it too.
   - If it doesn't exist: create it from template (see section below). Do NOT inject client specifics into the base.
4. **Map every variant to (dimension, value) pairs.**
   - Every base dimension must be resolved for every variant.
   - Unresolvable dimension → STOP. Either the variant is missing data (flag), or the dimension's allowed values are too narrow (add to base if truly generic, or to client overlay if domain-specific).
5. **Extract conversion rates per (variant, segment).** Decimals, not percentages. Include Control.
6. **Extract segments.** Name, n, weight as decimals summing to 1.0. Segment names stay verbatim from source — they're client-specific.
7. **Extract friction points.** For each: count out of n_total, variants involved, segment pattern, persistence (`resolved` / `introduced` / `introduced_then_removed` / `persistent` / `variant_specific`).
8. **Extract citations/quotes.** Attach each to a (segment, variant) pair.
9. **Extract aggregate metrics.** SUS, SEQ, sentiment, completion rate, etc. Preserve verbatim.
10. **Emit `data/<client>/element_matrix.json`.**
11. **Spot-check.** Pick 5 random (variant, dimension, value) entries. Verify against `data/<client>/source.md`. Require ≥ 4/5 agreement. If below, find the root cause (taxonomy bug? extraction error?) and re-run.
12. **Adversarial review.** Name the top 3 most-likely misclassifications, each with a failure mechanism and a fix path. Log to `tasks/findings.md` under a dated heading.
13. **Update `tasks/progress.md`** with what was parsed, N elements extracted, any taxonomy gaps found, and the spot-check round numbers.
14. **Append to `tasks/improvements.md`** any weaknesses found that can't be fixed now but should be tracked (adversarial findings #2 and #3 usually land here).

## Decision tree

- **Taxonomy gap** (source mentions an element type not in base or overlay):
  - If the gap is generic (would apply to a different domain too): add to base. Document the client that surfaced it.
  - If the gap is domain-specific: add to client overlay.
  - Never force-fit into an existing value.
- **Indistinguishable variants under taxonomy but clearly different in source**: taxonomy is under-specified. Add a dimension.
- **Element co-varies perfectly across every variant it appears in** (e.g., `blurred_card` always with `crown_header` in V2-V4): flag in `confounds[]`. Synthesizer must not single-attribute.
- **Source ambiguous** (e.g., "low-contrast CTA" without a color): record as `extraction_confidence: inferred`; do not guess a specific value.
- **Two clients independently needed the same overlay-only value**: promote to base. Remove from both overlays. Note the promotion in base file's "Open dimensions" section.

## Per-client taxonomy overlay template

When a new client arrives and has no existing overlay, create `.claude/rules/element-taxonomy-<client>.md` with these sections:

```markdown
# Element taxonomy — <Client> overlay

Version: 1.0. Pairs with `data/<client>/element_matrix.json`.

## Client context

<One paragraph — domain, vertical, what the activation screen is for, any regulatory context.>

## Overlay values (specific to this client's taxonomy)

<Lists any allowed values or sub-attributes not in the base — e.g., specific regulator names, specific evidence formats, client-specific cta_primary_label strings observed in source.>

## Client-only dimensions

<Dimensions meaningful only for this client's domain. Include rationale: why not in base.>

## Variant → (dimension, value) mapping

<Table: each variant × each dimension.>

## Extraction confidence

<Any inferred values.>

## Client-specific contradictions

<Rules like "urgency_mechanism=countdown_timer + segment skeptical_investor → negative" derived from this client's observations. Informs synthesize.>

## Proposed-but-untested values

<Base values the synthesizer may reach for but that have no observation data in this client's dataset. Each must carry a note about the expected mechanism so the synthesizer has a rationale it can cite.>
```

## Output schema (reference)

```jsonc
{
  "version": "1.0",
  "client": "<client-slug>",
  "source": { "url": "...", "extracted_at": "YYYY-MM-DD", "source_file": "data/<client>/source.md" },
  "taxonomy_base": ".claude/rules/element-taxonomy-base.md",
  "taxonomy_overlay": ".claude/rules/element-taxonomy-<client>.md",
  "n_total": 50,
  "segments": [
    { "id": "<snake_case>", "name": "<verbatim from source>", "n": 12, "weight": 0.24 }
  ],
  "variants": [
    {
      "id": "V4",
      "elements": {
        // every base dimension resolved, plus any overlay-only dimensions
      },
      "conversion_by_segment": { "<segment_id>": 0.25 }
    }
  ],
  "friction_points": [ /* { id, summary, count, of_total, variants, segment_pattern, persistence, notes? } */ ],
  "citations": [ /* { segment, variant, quote, context } */ ],
  "aggregate_metrics": { /* completion_rate, sus_score, seq_score, avg_sentiment, ... */ },
  "confounds": [ /* { elements[], variants_involved[], note } */ ],
  "clean_element_contrasts": [ /* { contrast, diff, observation, inference } */ ],
  "extraction_confidence": { /* "V2.cta_primary_label": "inferred" */ },
  "flags": [ /* strings with caveats weigh-segments/synthesize must see */ ]
}
```

## Success criteria

- Every base dimension resolved for every variant.
- Matrix validates as JSON.
- Weighted-overall conversion per variant reproduces source's published completion rate to ≤ 1pt rounding.
- Spot-check ≥ 4/5 agreement.
- Adversarial review logged with top-3 failure mechanisms + fix paths.
- Source file (`data/<client>/source.md`) is immutable from this point — future re-fetches go to versioned siblings.
- No client-specific content lands in `.claude/rules/element-taxonomy-base.md` or in this SKILL.md. All client context lives under `data/<client>/` or `.claude/rules/element-taxonomy-<client>.md`.

## Common pitfalls

- **Baking client segments into the skill.** Segments like "Skeptical Investor / Curious Beginner" are Univest-specific. Never reference them in this file, in the base taxonomy, or in sibling skills. Always read segments from the matrix.
- **Collapsing distinct elements into one value** (e.g., calling V1's sticky CTA and V4's sticky CTA the same when context differs). Fix: check every base dimension independently before mapping.
- **Inferring segment-level scores from variant-level data.** This skill stores observations, not inferences. Weighing happens downstream.
- **Silently dropping aggregate metrics.** Keep all of them; they may become inputs to the evaluator.
- **Rewriting the source file to "clean it up."** Source is immutable. Always.
- **Forcing taxonomy overlay content into base.** If it's domain-specific, it stays in the overlay — even if it feels redundant across two fintech clients. Only lift to base when a genuinely different vertical needs it too.

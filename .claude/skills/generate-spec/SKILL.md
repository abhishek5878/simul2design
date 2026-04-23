---
name: generate-spec
description: Trigger after synthesize, adversary, and estimate-conversion have all produced their outputs. Emits the final buildable specification document — the one an engineer reads and ships without re-asking. Every element choice gets a component name, field list, data source, and acceptance criteria. Operational preconditions from adversary are first-class. Client-agnostic.
---

# generate-spec skill

**The finish line.** Per IDEA.md problem 4: "A spec that says 'use a real trade card' is not buildable. A spec that says 'replace `blurred_trade_card` component with `ClosedTradeCard`, fields: `stock_name`, `entry_price`, `exit_price`, `days_held`, `rupee_gain`, sourced from `/api/trades/closed?limit=1&sort=recency`' is buildable." That's the bar.

Client-agnostic. Reads everything from `data/<client>/` artifacts. The skill never hardcodes client names or segment names.

## When to use

- All four inputs exist for this client: `element_matrix.json`, `weighted_scores.json`, `synthesized_variant.json`, `adversary_review.json`, `conversion_estimates.json`.
- Adversary's `summary.recommendation` is `proceed_to_spec_with_guardrails` OR `revise_with_conditions` (in which case the spec MUST encode the conditions as Operational Preconditions).

## When NOT to use

- If adversary's recommendation is `revise_synthesis` and synthesize has not yet re-run — the spec would encode an unfinished V(N+1). Run synthesize first.
- If the ask is a research summary or a narrative report — spec-writer's output is for engineers, not stakeholders. For stakeholder summaries, use the markdown companion files synthesize and adversary already produced.

## What "buildable" means here

A spec is buildable when a senior engineer who was NOT in any of the prior sessions can read it and:

1. Know **what components to create or modify**, by filename/class name if the codebase's convention is known, or by semantic name with a placeholder TODO if not.
2. Know **what data/API contracts each component needs**, with field names and types and example sources.
3. Know **what copy/text strings to use**, verbatim, with any dynamic placeholders named.
4. Know **what the acceptance criteria are**, framed as tests they can write.
5. Know **what operational disciplines must hold** for the design to deliver its predicted conversion. These are explicit hard prerequisites from adversary — if ops can't commit, the spec is not shippable.
6. Know **what instrumentation to add**, tied to the kill-conditions from estimate-conversion.

## Workflow

1. Read: matrix, weighted_scores, synthesized_variant, adversary_review, conversion_estimates.
2. **Client codebase context check.** If the client's repo / component conventions are known (asked user up-front, or detected from a linked repo), use them. If not, use semantic placeholders and annotate with `// TODO: match <client> codebase convention`.
3. **Produce the spec as `data/<client>/v<N+1>-spec.md`** using the structure below.
4. **Cross-check each section against adversary blockers** — every blocker must have a corresponding Operational Precondition or an explicit note of how the spec addresses it.
5. **Validate** that every predicted-conversion number in the spec is sourced from `conversion_estimates.json`, not from synthesize (estimator's intervals are the final authority).
6. **Update `tasks/progress.md`** with a one-paragraph hand-off to the client engineering team. Mark the plan for this feature as done.

## Spec document structure

```markdown
# V<N+1> — Buildable spec for <Client> <surface>

> **Source evidence:** `data/<client>/element_matrix.json`, `weighted_scores.json`, `synthesized_variant.json`, `adversary_review.json`, `conversion_estimates.json`.
> **Spec generated:** YYYY-MM-DD
> **Predicted weighted-overall conversion:** estimator-point (range low–high). Baseline: V(N) at X%.

## 0. Executive summary (1 paragraph for PM / skim)

<Goal. What ships. Predicted lift. Confidence. Operational preconditions count.>

## 1. Changes from V(N) (the diff)

For every changed dimension:

### 1.<n> <Dimension name> — V(N) `<old>` → V<N+1> `<new>`

- **What changes visually / behaviorally:** 1-3 sentences, concrete.
- **Replaces component:** `<OldComponent>` (current name in client codebase OR semantic name).
- **New component:** `<NewComponent>`, spec below.
- **Citation from evidence:** <friction_point id / clean_contrast ref / overlay mechanism>. Verbatim quote.
- **Expected per-segment impact:** from conversion_estimates.

## 2. Component specifications

For each new or modified component:

### `<ComponentName>`

**Purpose:** <one sentence>.

**Fields / props:**
| Name | Type | Source | Example |
|---|---|---|---|
| ... | ... | ... | ... |

**Copy strings (verbatim):**
- Primary: `"<exact text>"`
- Secondary: `"<exact text>"`
- Empty / loading / error states: explicit.

**Data contract:**
```
<endpoint or source>
Returns: <schema>
Staleness rule: <freshness constraint>
Fallback: <what to render if unavailable>
```

**Acceptance criteria (engineer writes these as tests):**
- [ ] <specific behavior assertion>
- [ ] <data-validity assertion>
- [ ] <failure-mode assertion>

## 3. Copy book (centralized for translation / legal / brand review)

All user-facing strings, in one place:

| Key | Text | Length | Reviewer gate |
|---|---|---|---|
| `activation.title` | ... | ... | — |
| `activation.cta.primary` | ... | ... | **legal** (per adversary obj-001 if relevant) |
| ... | | | |

## 4. Operational preconditions (hard prerequisites)

From adversary's blockers. **If Univest / the client team cannot commit to these, the spec is not shippable — descope first.**

- [ ] **Precondition 1:** <named operational discipline>. Owner: <team/role>. Measurable: <how to verify before ship>.
- [ ] **Precondition 2:** ...

## 5. Instrumentation (tied to kill-conditions)

From conversion_estimates's per-segment kill-conditions. Each one becomes an observation-layer metric:

- Event: `<event_name>`. Triggered on: <interaction>. Properties: <what to log>. Evaluated as: <kill-condition threshold>.

## 6. Predicted conversion (by segment, with kill-conditions)

From conversion_estimates. Explicit interval + named failure mode per segment.

## 7. Rollout recommendation

- Roll schedule (e.g., 10% → 50% → 100% over 2 weeks).
- A/B alternatives to run alongside (e.g., V5a green vs V5b muted_premium per adversary obj-005).
- Stop-ship criteria (which kill-conditions trigger a rollback).

## 8. What this spec deliberately does NOT prescribe

Sections the spec leaves open because the evidence did not support a strong recommendation:

- `<dimension>`: confounded / non-informative in the dataset. Spec adopts V(N)'s value unchanged with no strong rationale. If changed, requires a separate test.

## 9. Cross-references

- `data/<client>/synthesized_variant.md` — human-readable narrative for PM review.
- `data/<client>/adversary_review.json` — structured objections, overruled and accepted.
- `data/<client>/conversion_estimates.json` — prediction intervals and kill-conditions.
- `data/<client>/element_matrix.json` — the raw evidence.
```

## Success criteria

- Every element-change section has: component name, fields/props, data contract, copy strings, acceptance criteria.
- Every adversary blocker appears in Operational Preconditions.
- Every predicted conversion number is traceable to conversion_estimates (not synthesize).
- Every kill-condition has a corresponding instrumentation event.
- A senior engineer who has read nothing else can read this spec and produce an implementation plan in < 30 minutes.
- Section 8 exists: the spec is honest about what it doesn't prescribe.

## Common pitfalls

- **Vague component names.** "Trust card component" is not buildable. "`ClosedTradeCard` with fields {stock_name, entry_price, exit_price, days_held, rupee_gain}" is.
- **Copy left as placeholders.** "<refund SLA copy>" in the spec is a TODO the engineer will shrug at. Write the exact string or mark it `needs_copywriting_input`.
- **Burying preconditions in prose.** Operational preconditions must be a checkbox list — gates for the ship decision.
- **Over-specifying.** The spec doesn't need to dictate CSS, library choices, or code patterns that the client's codebase already has conventions for. Specify the semantic contract, not the implementation.
- **Missing failure-mode instrumentation.** Every kill-condition from estimate-conversion must have an observable event. Otherwise we can't detect failure post-ship.

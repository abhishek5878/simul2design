# Plan — variant image rendering (`simul2design.render`)

## Goal

Close the gap captured in `tasks/lessons.md`:
> "Proper design" means a visual artifact the reader can see, not only a
> markdown spec — `generate-spec` output is the spec doc; parallel artifact
> `design/<variant>.png` is the visual. Ship both.

Add a render step to `SynthesisPipeline` that takes the `synthesized_variant`
JSON (chosen taxonomy values per dimension) and produces a PNG mockup of the
V(N+1) screen. Engineer reads the spec markdown AND looks at the image.

## Design decisions

### Why HTML → PNG via Playwright

- **Deterministic.** Pure CSS layout from a known taxonomy. Same input → same
  pixels. No image-model hallucination.
- **Inspectable.** The HTML is the source of truth — a designer or PM can open
  it in any browser to interact with the mockup before it's flattened to PNG.
- **Cheap.** Zero LLM cost. Playwright + headless Chromium runs locally.
- **Faithful enough.** The taxonomy tells us layout/CTA stack/copy/urgency/
  trust signals. A flex-grid HTML mock that places each element by its enum
  value is a serviceable wireframe — better than nothing, and good enough for
  an engineer to see the shape.

### What we are NOT doing

- Pixel-perfect Figma rendering. (Different problem; option 3 from the
  proposal — separate v0.3.0 if desired.)
- Image-model generation (DALL-E / Midjourney). Lossy and non-reproducible.
- Multiple device sizes by default. Single 375×812 mobile mockup is the
  baseline; add `--viewport-width/-height` flags for callers who need others.

### Module layout

```
simul2design/render/
  __init__.py                # exports render_variant_png, render_variant_html
  html_template.py           # pure Python: synthesized_variant dict → HTML string
  visual.py                  # Playwright wrapper: HTML string → PNG bytes
  template_assets/
    base.css                 # design tokens + layout primitives
```

`html_template.py` is the heart of the work. It has no Playwright dependency
and is fully unit-testable without a browser. `visual.py` is the thin browser
adapter: it spins up Chromium, sets viewport, screenshots the rendered HTML.

### Pipeline integration

```python
SynthesisPipeline(
    run_render_visual=True,          # default False (backward-compat)
    render_viewport=(375, 812),       # mobile default
    render_output_dir=None,           # if None, returns bytes only
)
```

New field on `SynthesisResult`:
- `variant_image_png_bytes: Optional[bytes] = None` — raw PNG bytes (in-memory)
- `variant_image_path: Optional[str] = None` — file path if `render_output_dir`
  was set; engine wires this to Cloudinary upload separately

The renderer is OPT-IN; existing flows keep working unchanged.

### CLI

```bash
simul2design-render <result.json> -o variant.png \
    [--viewport 375x812]             # default: 375x812 mobile
```

Reads a `SynthesisResult` JSON, extracts `synthesized_variant`, renders, writes
PNG. Useful for re-rendering after tweaking the HTML template without
re-running the cascade.

### Dependency strategy

Playwright is heavy (~150MB Chromium binary). Approach:

1. Add as an OPTIONAL extra: `pip install simul2design[render]` installs
   playwright but the default install does not.
2. Lazy import inside `visual.py` — `import playwright` happens at first
   render call, not at module load. Importing `simul2design` without the
   render extra works fine; only `render_variant_png` raises a friendly error
   instructing the caller to `pip install simul2design[render] && playwright
   install chromium`.
3. The pure-Python `html_template.py` has no playwright dep and is always
   importable. Callers who want HTML-only (e.g. embed in a web UI) skip the
   browser entirely.

### Taxonomy → HTML mapping

The `synthesized_variant.elements` dict has per-dimension values from the
client overlay's enum. The template maps each value to a CSS/HTML pattern:

| Dimension | Value → HTML pattern |
|---|---|
| `layout` | `full_screen` → root `flex column 100vh`; `bottom_modal` → root + sticky bottom card; `full_screen_dark` → `bg-#0a0a0a text-white`; `inline` → no chrome; `side_panel` → right-aligned 80% width drawer |
| `branding` | `crown_header` → top bar with crown icon; `logo_only` → top bar with logo placeholder; `none` → no top bar |
| `price_visibility` | `visible_primary` → price chip on CTA; `visible_with_framing` → price banner above CTA with framing copy; `opaque` → price omitted |
| `cta_primary_label` | freeform string → button text verbatim |
| `cta_style` | enum → button background / border classes |
| `cta_stack` | `single` → one button; `dual_outline_plus_sticky` → outline button + sticky bottom button; `dual_side_by_side` → two equal buttons; `primary_plus_secondary_link` → button + text link below |
| `urgency_mechanism` | `countdown_timer` → live timer above CTA; `scarcity_count` → "only N left" chip; `social_proof_realtime` → "N viewing now" chip; `deadline_text` → static end date; `none` → omit |
| `refund_or_guarantee_copy` | maps to a small badge + text block above/below CTA |
| `trust_signal` | `regulatory` → regulator badge; `evidence_mode` → "as seen in" or stat chip; `regulatory_plus_evidence` → both stacked |
| `evidence_detail` | sub-element of trust_signal; e.g. `aggregate_metric` → stat block; `named_past_outcome` → testimonial chip with metric |

Unknown taxonomy values render as a labeled placeholder rectangle so the
engineer immediately sees what was intended but not yet templated. The
template never silently omits a dimension.

### Output content

Below each rendered section, a small footer overlay (toggleable) shows:
- variant name (e.g. "V_next")
- timestamp
- the source dimension → value mapping that produced each block

Footer is OFF by default for the spec PNG; ON when generated for internal
review.

## Phases

### Phase 1 — pure HTML template (status: pending)

- [ ] `simul2design/render/html_template.py`:
  - `def render_variant_html(synthesized_variant: dict, *, footer: bool = False) -> str`
  - Loads `base.css` from package data via `importlib.resources`
  - Maps every dimension in `BASE_DIMENSIONS` (from `taxonomy_data/element-taxonomy-base.md`)
  - Unknown / freeform values render as labeled placeholder
- [ ] `simul2design/render/template_assets/base.css`
- [ ] `simul2design/render/__init__.py` exports `render_variant_html`

### Phase 2 — Playwright PNG renderer (status: pending)

- [ ] `simul2design/render/visual.py`:
  - `def render_variant_png(synthesized_variant: dict, *, viewport=(375, 812),
    footer=False, output_path=None) -> bytes`
  - Lazy-imports playwright; raises `RenderUnavailableError` with install hint
    if missing
  - Uses sync API (`playwright.sync_api.sync_playwright`) — async overhead not
    worth it for a single screenshot
- [ ] `simul2design/render/__init__.py` adds `render_variant_png`,
  `RenderUnavailableError`

### Phase 3 — pipeline integration (status: pending)

- [ ] Add `run_render_visual: bool = False`, `render_viewport: tuple[int, int]`,
  `render_output_dir: Optional[str]` to `SynthesisPipeline.__init__`
- [ ] After cascade, if enabled, call `render_variant_png(...)` and attach
  to `SynthesisResult.variant_image_png_bytes` (and write to
  `render_output_dir/{client_slug}-v_next.png` if provided, populating
  `variant_image_path`)
- [ ] `SynthesisResult` schema: add `variant_image_png_bytes: Optional[bytes]`
  and `variant_image_path: Optional[str]`

### Phase 4 — CLI + extras (status: pending)

- [ ] `scripts/render-variant.py` (the CLI body)
- [ ] `pyproject.toml`: add `[project.optional-dependencies] render = ["playwright>=1.45"]`
  and `[project.scripts] simul2design-render = "scripts.render_variant:main"`
  (or move to `simul2design.render.cli:main` for in-package import)

### Phase 5 — tests (status: pending)

- [ ] `scripts/test-render-visual.py`:
  - HTML template tests (no browser) — assert each taxonomy value produces a
    known HTML pattern
  - Test placeholder rendering for unknown values
  - Skip the actual Playwright PNG step unless `RUN_BROWSER_TESTS=1` to keep
    CI fast
- [ ] One end-to-end test that does run browser: ingest the prior cascade's
  `synthesized_variant`, render PNG, assert PNG header bytes + non-trivial
  size

### Phase 6 — release (status: pending)

- [ ] Bump `__version__` to `0.2.0` in `simul2design/__init__.py` and
  `pyproject.toml`
- [ ] Update `INTEGRATION.md` §10 with the render section
- [ ] Commit, push, tag `v0.2.0`
- [ ] Engine PR (separate, follow-on): if the engine wants to surface the
  image in `synthesis_ready`, expose `variant_image_path` (already populated)
  and let the engine upload to Cloudinary or return as base64

## Errors Encountered

| Phase | Error | Resolution |
|---|---|---|
| _(empty)_ | _(none yet)_ | _(none yet)_ |

## Out of scope for v0.2.0

- Multi-screen flow rendering. The cascade only synthesizes a single V(N+1)
  screen today; multi-screen would require synthesizing per-screen variants
  first.
- A11y rendering audit. The HTML is for visual review, not for handoff to a
  screen-reader testing pipeline.
- Figma integration.
- Image diffing (V(N) baseline vs V_next overlay) — useful but separate
  feature.

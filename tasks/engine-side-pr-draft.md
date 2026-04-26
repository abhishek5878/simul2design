# Engine-side PR: wire `simul2design` synthesis as a follow-on event

## Goal

Drop the `simul2design` synthesis cascade into `apriori_simulation_engine` as
a non-blocking follow-on to the `comparison_ready` event in
`MultiFlowOrchestrator.stream_events()`. Frontend renders the `AbReport`
immediately; ~4 min later a `synthesis_ready` event arrives carrying the V(N+1)
spec. Failure of the cascade does NOT block or corrupt the `comparison_ready`
event.

## Diff 1 — `requirements.txt`

```diff
+ # Multiverse Synthesis Engine — turns AbReport into a buildable V(N+1) spec.
+ # Pinned to a specific commit until 0.1.0 ships to PyPI.
+ simul2design @ git+https://github.com/abhishek5878/simul2design.git@<commit-sha>
```

(Use the commit SHA after pushing simul2design's main; once we ship to PyPI we
can switch to `simul2design==0.1.0`.)

## Diff 2 — `src/core/multiflow_orchestrator.py`

```diff
@@ -32,6 +32,8 @@
 import httpx

+from simul2design.langgraph_node import synthesis_node
+from simul2design import SynthesisPipeline
 from src.core.ab_report_synthesis import assemble_ab_report
 from src.core.dag_flow import DAGFlow, dag_flow_from_dict
 from src.core.langgraph_orchestrator import simulation_orchestrator
 from src.utils.config import BASE_DIR

 logger = logging.getLogger(__name__)


+# Construct once at module import — anthropic client + auth resolve at first use.
+_synth_pipeline = SynthesisPipeline(
+    run_full_cascade=True,
+    max_llm_cells=20,
+)
+
+
+SYNTHESIS_FEATURE_FLAG = "SIMUL2DESIGN_ENABLED"
+
+
@@ -274,6 +286,30 @@
             yield json.dumps({
                 "type": "comparison_ready",
                 "data": report,
             }) + "\n"

+            # Multiverse Synthesis (simul2design) — opt-in via env flag.
+            # Runs AFTER comparison_ready so the frontend already has the AbReport.
+            # Cascade is ~4 min, ~$0.45 per run; failures are isolated and do
+            # NOT corrupt the comparison_ready stream above.
+            if os.environ.get(SYNTHESIS_FEATURE_FLAG, "").lower() in ("1", "true", "yes"):
+                try:
+                    synth_state = {
+                        "ab_report": report,
+                        "client_slug": client_label or "default",
+                    }
+                    synth_out = await synthesis_node(synth_state, pipeline=_synth_pipeline)
+                    yield json.dumps({
+                        "type": "synthesis_ready",
+                        "data": {
+                            "synthesis_input_source": synth_out.get("synthesis_input_source"),
+                            "ready_for_human": synth_out.get("synthesis_ready_for_human"),
+                            "result": synth_out.get("synthesis_result"),
+                        },
+                    }) + "\n"
+                except Exception as e:
+                    logger.error("simul2design synthesis failed: %s", e, exc_info=True)
+                    yield json.dumps({
+                        "type": "synthesis_failed",
+                        "data": {"message": str(e), "comparison_id": comparison_id},
+                    }) + "\n"
+

 # Global singleton
 multiflow_orchestrator = MultiFlowOrchestrator()
```

(Add `import os` at the top with the other stdlib imports if not already present.)

## Diff 3 — frontend event handling (`apriori_landing`, optional)

The `synthesis_ready` event is new. Until the landing repo handles it, it
will appear as an unknown NDJSON line that the existing reader should
ignore. To render the V(N+1) spec, add a handler in
`src/lib/stream-simulation.ts` that switches on `type: "synthesis_ready"`
and either stores the markdown for an in-app viewer or routes to a
`/simulations/.../synthesis` page.

This is non-blocking — the engine PR can merge first and the landing PR
follows independently.

## Tests to add to the engine

Add to `tests/unit/test_multiflow_orchestrator.py`:

1. `test_synthesis_ready_NOT_emitted_when_flag_disabled` — without the env
   flag, no `synthesis_ready` event in the stream.
2. `test_synthesis_ready_emitted_after_comparison_ready_when_enabled` — set
   `SIMUL2DESIGN_ENABLED=1`, mock `synthesis_node` to return a canned dict,
   assert event order: `comparison_ready` then `synthesis_ready`.
3. `test_synthesis_failure_does_not_block_comparison_ready` — patch
   `synthesis_node` to raise; assert `comparison_ready` still emitted and a
   `synthesis_failed` event follows.

Keep the live-cascade test out of CI (cost). Run it manually before each
release with the same fixture in
`/Users/abhishekvyas/Desktop/simul_design/scripts/test-ab-report-adapter.py`.

## Rollout sequence

1. Merge `simul2design` adapter v1.1.0 to its main; tag SHA.
2. Open this engine PR with the SHA pinned.
3. Land it with `SIMUL2DESIGN_ENABLED=` (unset) — code is dormant in prod.
4. Pick one staging client (`loop_health` or `blink_money`), set the flag
   in that environment only, run one real comparison, inspect the
   `synthesis_ready` payload.
5. If the spec is coherent and useful: enable the flag for all staging
   clients, watch for a week, then promote to prod.
6. Add the `synthesis_ready` handler to the landing repo once the engine
   is reliably emitting it.

## Why a follow-on event, not an inline merge into `comparison_ready`

Inline would block the AbReport on the synthesis cascade — frontend would
spin for 4+ minutes before seeing anything. The follow-on pattern lets the
existing AbReport UX stay sub-30s while the synthesis is a progressive
enhancement that arrives later. The pattern matches the SSE event-stream
shape the engine already uses (`flow_insights_ready` per flow,
`comparison_ready` aggregate) — it's idiomatic, not additive churn.

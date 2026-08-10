# Human-Centric Benchmark Integration Skeleton

Branch: `dynamic-human-benchmark-implementation`

This GN0 branch is for the evaluation and RL side of the benchmark. The data
generation side should live in `Navdp_Datagen_Pathplanner` under
`Code/navdp/benchmark/`.

## Two-Part Implementation Split

1. **NavDP Pathplanner datagen**
   - Produces scenario JSON, fixture data, split manifests, and training-data
     supervision.
   - Owns scene selection, actor/mission generation, and deterministic fixture
     authoring.

2. **GN0 + GN-Bench-Tools evaluation/RL**
   - Consumes NavDP-generated scenarios.
   - Owns deterministic replay, social metrics, baseline policies, and RL task
     wrappers.
   - Skeleton files are in:
     - `GN-Bench-Tools/GN_Bench/human_eval/`
     - `GN-Bench-Tools/GN_Bench_baselines/human_eval/`

## Immediate TODOs

- Navigation model evaluation inventory and the checkpoint-gated new-model
  shortlist are tracked in `docs/navigation_model_evaluation_research.md`.
- Use `eval_navdp_missions.py` for replay-only NavDP mission smoke evaluation
  across generated examples:
  `python3 eval_navdp_missions.py --source /Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples --result-path tmp/navdp_human_eval`.
- Use `vln_model_registry.py` to list checkpoint-gated newer VLN candidates:
  `python3 vln_model_registry.py --bucket new_post_2025 --native-runnable --json`.
- Use `plan_vln_evaluations.py` to produce a model-run plan against NavDP
  mission examples:
  `python3 plan_vln_evaluations.py --bucket new_post_2025 --native-runnable --summary`.
- Use `vln_adapter_registry.py` to inspect adapter/checkpoint readiness and
  concrete dispatch commands:
  `python3 vln_adapter_registry.py --bucket new_post_2025 --summary`.
- Use `prepare_vln_checkpoints.py` to generate checkpoint fetch commands without
  downloading by default:
  `python3 prepare_vln_checkpoints.py --bucket new_post_2025 --native-runnable --missing-only --json`.
- Use `export_vln_adapter_inputs.py` to export compact, model-facing per-mission
  records for native adapter authors:
  `python3 export_vln_adapter_inputs.py --source /Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples --result-path tmp/vln_adapter_inputs`.
- Use `run_vln_native_eval.py` as the unified dispatcher for replay, GN-BAE,
  and future native Python adapters:
  `python3 run_vln_native_eval.py --model human_eval_json_policies --mission-source /Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples --result-path tmp/navdp_human_eval`.
- Use `vln_eval_results.py` to normalize replay, native, or external-reported
  model outputs into one result schema:
  `python3 vln_eval_results.py --model human_eval_json_policies --from-replay-summary tmp/navdp_human_eval/summary.json --json`.
- Python adapters dispatched by `run_vln_native_eval.py` also write the same
  normalized `vln_result.json` row, using their `VLNAdapterRunResult.metrics`
  or summary JSON as input.
- Native model adapters should consume `adapter_inputs.jsonl` from
  `export_vln_adapter_inputs.py` for instructions, robot starts, goals, humans,
  scene references, and mission metadata instead of re-parsing raw NavDP JSON.
- Replay-only evaluator support is complete for the eight generated NavDP
  mission families: `deliver_to_human`, `navigate_with_social_constraints`,
  `human_guided_uncertain_region`, `serve_queue`, `mission_stream`,
  `dense_dynamic_humans`, `dense_multi_robot`, and
  `dense_dynamic_combined`.
- `HumanCentricRLTask` now exposes replay-backed observations, JSON action
  validation, and terminal reward components derived from deterministic replay
  metrics.
- `HumanCentricTask-v0` is registered for full GN-Bench environments and exposes
  replay helpers plus simulator config mapping; full `Env` reset/step remains a
  simulator-dependency smoke gate.
- Wire `GN_Bench.human_eval.NavDPScenarioAdapter` into the full simulator task
  path after replay-backed task semantics are accepted.
- Connect the five implemented baseline policies in `GN_Bench_baselines.human_eval`
  to simulator-backed rollouts after the JSON assignment sweep is accepted.
- Add native adapter implementations for checkpoint-gated VLN model candidates,
  starting with GN-BAE reproduction and then FutureNav/AwareVLN/GA-VLN once
  checkpoints and observation adapters are available. The adapter contract,
  dispatcher, checkpoint fetch planner, and non-runnable model-specific stubs
  now exist; real model adapters/checkpoints are still open.
- Keep naming flexible until the benchmark title and package names are frozen.

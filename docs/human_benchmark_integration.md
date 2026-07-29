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

- Wire `GN_Bench.human_eval.NavDPScenarioAdapter` into a dataset loader.
- Implement deterministic replay in `HumanCentricEvaluator`.
- Convert replay metrics into RL rewards in `HumanCentricRLTask`.
- Implement the five baseline policies in `GN_Bench_baselines.human_eval`.
- Keep naming flexible until the benchmark title and package names are frozen.

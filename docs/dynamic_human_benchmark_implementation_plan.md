# Dynamic Human Benchmark Implementation Plan

Current branch: `dynamic-human-benchmark-implementation`
Date: 2026-07-01

## Mission

Build the Human-Centric Mission Stream Navigation Benchmark: a multi-robot
navigation benchmark where humans are active, stateful entities with identity,
roles, trajectories, dialogue state, service needs, and social constraints.

The benchmark should evaluate more than route following. A planner receives
missions over time, assigns one or more robots, reacts to human and mission
state changes, and completes tasks while respecting queues, conversation groups,
pedestrian flows, vulnerable-human buffers, and personal-space rules.

## Repository Responsibilities

### NavDP Pathplanner

Path: `/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner`

Owns data generation and benchmark artifact production:

- scenario JSON schema and parser;
- fixture and generated-example scenarios;
- scene selection and pilot split manifests;
- human, robot, mission, trajectory, and social-structure generation;
- dynamic-human scenario configs;
- collision, distance, and spacing validation during generation;
- training/evaluation dataset packaging.

Relevant current files:

- `docs/human_centric_mission_stream_benchmark.md`
- `docs/human_centric_benchmark_todos.md`
- `docs/navdp_data_plan.md`
- `Code/navdp/benchmark/schema.py`
- `Code/navdp/benchmark/validation.py`
- `Code/navdp/benchmark/cli.py`
- `Code/navdp/benchmark/example_generation.py`
- `configs/benchmark/human_centric_mission_stream/`

### GN0 And GN-Bench-Tools

Paths:

- `/Users/dongjk/ProjectFiles/GN0`
- `/Users/dongjk/ProjectFiles/GN0/GN-Bench-Tools`

Owns benchmark consumption, evaluation, RL, and baselines:

- NavDP scenario adapter and split loader;
- deterministic sync replay;
- mission success and social metrics;
- RL task wrapper and reward mapping;
- baseline policies;
- evaluation reports and paper-facing metric summaries.

Relevant current files:

- `GN-Bench-Tools/GN_Bench/human_eval/scenario_adapter.py`
- `GN-Bench-Tools/GN_Bench/human_eval/evaluator.py`
- `GN-Bench-Tools/GN_Bench/human_eval/social_metrics.py`
- `GN-Bench-Tools/GN_Bench/human_eval/rl_task.py`
- `GN-Bench-Tools/GN_Bench_baselines/human_eval/policies.py`
- `docs/human_benchmark_integration.md`

## Current Implementation Status

NavDP producer status is tracked in the NavDP repo by the separate Codex owner.
For GN0/GN-Bench-Tools, assume NavDP emits scenario JSON and split manifests;
this repo consumes those artifacts and must remain tolerant of additive producer
schema changes.

Completed or scaffolded in GN0/GN-Bench-Tools:

- GN-Bench-Tools evaluation/RL/baseline skeletons exist.
- `NavDPScenarioAdapter` can load a single scenario JSON and a draft split
  manifest into a lightweight `HumanCentricEpisode`.
- `HumanCentricEvaluator` exists but still returns empty replay results.
- Social metric classes exist as placeholders.
- RL task wrapper exists as a placeholder.
- Deterministic JSON-level baseline policies are implemented for:
  - oracle human-centric assignment;
  - greedy nearest assignment;
  - priority/deadline greedy assignment;
  - no-human-awareness shortest-static-path behavior;
  - single-robot serial execution.

Verified on 2026-07-01:

- Baseline policy module compiles.
- All five policies emit deterministic `BaselineAction` records on the current
  NavDP generated mission-stream example.

## Required Components

### Scenario Contract

- Stable schema version.
- Scene asset references.
- Robot roster with capabilities, start pose, sensors, and embodiment.
- Human roster with identity, role, appearance, SMPL-X/action assets, behavior
  state, trajectories, dialogue/persona hooks, and social defaults.
- Mission stream with release times, deadlines, priority, targets,
  dependencies, cancellation/update state, and success conditions.
- Social structures with typed geometry and rules.
- Event log for deterministic replay.
- Expected result records for fixtures and regression tests.

### Mission Families

The design defines ten families:

1. Correct human delivery.
2. Human-aware interaction.
3. Human-guided search.
4. Implicit need fulfillment.
5. Escort and rendezvous.
6. Queue and priority service.
7. Interruption recovery.
8. Multi-robot handoff.
9. Conflict resolution.
10. Group interview mission stream.

The MVP implementation can start with four schema-supported types:

- `deliver_to_human`
- `navigate_with_social_constraints`
- `serve_queue`
- `mission_stream`

The schema should still reserve names for the remaining families before public
release to avoid migration churn.

### Dynamic Human Layer

- Human trajectory generation and retiming.
- Behavior timelines for walking, waiting, waving, loitering, queueing,
  blocking, and interacting.
- SMPL-X/action sequence references for rendered or simulated humans.
- Appearance and attribute tags for target identification.
- Dialogue/persona profiles for guided search and implicit-need tasks.
- Per-human social defaults, including personal-space and vulnerable buffers.

### Social Metrics

- Human-robot minimum distance.
- Collision and near-miss counts.
- Personal-space violation duration.
- Vulnerable-human buffer violation.
- Queue service-order violation.
- Queue cutting or segmentation.
- F-formation protected-center crossing.
- Pedestrian-flow reverse traversal.
- Right-side yielding failures.
- Excessive blocking, freezing, or oscillation.

### Baselines

- Oracle human-centric planner.
- Greedy nearest mission assignment.
- Priority/deadline greedy assignment.
- No-human-awareness shortest path planner.
- Single-robot serial execution.

## Gaps

GN0/GN-Bench-Tools gaps only:

- Scenario adapter does not yet produce a GN-Bench `Episode` subclass or normal
  dataset entries.
- No registered `HumanCentric-v0` dataset exists.
- GN-Bench deterministic evaluator returns empty metrics and no success result.
- Social metric classes are placeholders.
- Baseline policies are JSON-level and not yet connected to a runner, RL task,
  or GN-Bench environment.
- RL wrapper has no real observation, transition, reward, or simulator binding.
- No registered `HumanCentricTask-v0` task or measure wrappers exist.
- Simulator/render binding for dynamic humans is not implemented.
- Split manifest format is still coordinated with the NavDP producer owner.

## Timeline And Todos

### By Thursday 2026-07-02

Goal: freeze the GN0/GN-Bench-Tools consumer target and unblock evaluator work.

- [x] Update GN0 docs to reference
  `dynamic-human-benchmark-implementation`.
- [x] Document that NavDP schema/datagen work is owned by the separate NavDP
  Codex owner.
- [x] Implement first JSON-level deterministic baseline policies.
- [x] Smoke-test all five baseline policies on a current NavDP generated
  mission-stream example.
- [ ] Define the GN-Bench consumer contract for NavDP scenarios:
  required fields, optional fields, fallback defaults, and version tolerance.
- [ ] Draft the split manifest fields GN-Bench needs from NavDP.

### By Thursday 2026-07-09

Goal: make GN-Bench able to load NavDP scenarios as normal episodes.

- [ ] Add `GN_Bench/human_eval/dataset.py`.
- [ ] Register `HumanCentric-v0` with GN-Bench dataset registry.
- [ ] Make `HumanCentricEpisode` compatible with `GN_Bench.core.dataset.Episode`
  while preserving raw scenario payload in `info["human_scenario"]`.
- [ ] Resolve scenario paths relative to split manifests.
- [ ] Map NavDP scene assets to GN-Bench `scene_id`, `ref_json`, start position,
  and start rotation.
- [ ] Add adapter/dataset smoke tests using current generated examples.

### By Thursday 2026-07-16

Goal: implement first real GN-Bench replay and metrics.

- [ ] Wire `NavDPScenarioAdapter` into a usable dataset/split loader.
- [ ] Implement deterministic sync replay over timestamped robot and human
  trajectories.
- [ ] Implement mission completion metrics:
  - success/failure;
  - deadline satisfaction;
  - correct recipient/target;
  - per-mission status.
- [ ] Implement first social metrics:
  - minimum robot-human distance;
  - collision count;
  - personal-space violation count/duration;
  - vulnerable-buffer violation;
  - queue service-order violation.
- [ ] Emit replay traces that can be inspected in failures.

### By Thursday 2026-07-23

Goal: connect metrics, baselines, and replay into a pilot runner.

- [ ] Implement first social metrics:
  - minimum robot-human distance;
  - collision count;
  - personal-space violation count/duration;
  - vulnerable-buffer violation;
  - queue service-order violation.
- [ ] Connect all five JSON-level baselines to a split runner.
- [ ] Emit per-policy replay results as JSON.
- [ ] Produce a pilot result table with success, deadline, collision, and social
  violation metrics.
- [ ] Define how baseline `BaselineAction` maps into the future RL task action
  contract.

### By Thursday 2026-07-30

Goal: expose the benchmark through GN-Bench task/RL interfaces.

- [ ] Implement `HumanCentricRLTask` observation contract.
- [ ] Implement RL action contract for assign/reassign/subgoal/interact/no-op.
- [ ] Convert replay metrics into RL reward components.
- [ ] Add `GN_Bench/human_eval/task.py`.
- [ ] Register `HumanCentricTask-v0`.
- [ ] Add minimal measure wrappers if needed for `env.get_metrics()`.
- [ ] Smoke-test `env.reset()` and one `env.step()` on a fixture episode.

### By Thursday 2026-08-06

Goal: stabilize GN-Bench consumer side for AAAI-27 reporting.

- [ ] Lock GN-Bench consumer contract for the NavDP-produced v0 scenario schema.
- [ ] Lock pilot split loading and reproducibility assumptions.
- [ ] Add paper-facing metric summaries from GN-Bench evaluator outputs.
- [ ] Add failure-case replay traces and visualization hooks.
- [ ] Document simulator/rendered-observation limitations and next scale-up plan.

## Immediate Next Engineering Actions

1. Update `docs/human_benchmark_integration.md` to use the current branch name.
2. Add the missing one-page schema summary in NavDP.
3. Add the pilot scene shortlist in NavDP.
4. Implement GN-Bench split loading against the generated NavDP manifest.
5. Implement deterministic replay for static fixture trajectories before adding
   dynamic-human path generation.

The safest implementation order is schema and fixtures first, replay second,
metrics third, baselines fourth, and large-scale dynamic-human generation last.

## Module-By-Module Implementation Breakdown

This section covers only GN0 and GN-Bench-Tools work. NavDP schema, validation,
example generation, pilot scene selection, and dynamic-human datagen are owned
by the NavDP Pathplanner Codex owner. This repo consumes those artifacts.

### GN-Bench-Tools: `GN_Bench/human_eval/scenario_adapter.py`

Purpose: bridge NavDP scenario JSON into GN-Bench episodes.

Work to do:

- Convert the lightweight `HumanCentricEpisode` into a GN-Bench-compatible
  episode representation.
- Preserve raw scenario payload in `episode.info["human_scenario"]`.
- Resolve scenario paths relative to split manifests.
- Map NavDP scene assets into GN-Bench `scene_id` and `ref_json` conventions.
- Derive start position/rotation from the first robot start pose.
- Be tolerant of additive NavDP schema fields.

Acceptance checks:

- Adapter loads current generated examples.
- Episode exposes scenario id, scene id, start pose, raw payload, and source
  scenario path.

### GN-Bench-Tools: Dataset Registration

Purpose: make human benchmark episodes load through normal GN-Bench config.

Work to do:

- Add `GN_Bench/human_eval/dataset.py`.
- Implement `HumanCentricDataset`.
- Register it as `HumanCentric-v0`.
- Load scenario paths from split manifests or direct scenario lists.
- Import dataset registration from `GN_Bench/human_eval/__init__.py`.

Acceptance checks:

- `make_dataset("HumanCentric-v0", config=...)` returns non-empty episodes.
- Existing GN-Bench episode iterator can iterate the dataset.

### GN-Bench-Tools: `GN_Bench/human_eval/evaluator.py`

Purpose: authoritative deterministic sync evaluator.

Work to do:

- Build replay timeline from mission events and actor trajectories.
- Compute released/assigned/completed/timed-out mission state.
- Invoke social metric modules on replay state.
- Return aggregate metrics, per-mission metrics, event trace, violation trace,
  and deterministic success boolean.

Acceptance checks:

- Minimal passing fixture returns `success=True`.
- Repeated runs are byte-stable for the same input.

### GN-Bench-Tools: `GN_Bench/human_eval/social_metrics.py`

Purpose: compute reusable social/safety metrics from replay state.

Work to do:

- Define shared replay-state input contract.
- Implement human-distance, vulnerable-buffer, queue-order, F-formation, and
  pedestrian-flow metrics incrementally.
- Keep metric names stable for paper tables and RL rewards.

Acceptance checks:

- Each metric class has a tiny pure-Python fixture.
- Evaluator emits metric names consistently across scenarios.

### GN-Bench-Tools: `GN_Bench_baselines/human_eval/policies.py`

Purpose: deterministic baselines for pilot evaluation.

Current state:

- JSON-level implementations exist for oracle, greedy nearest, priority greedy,
  no-human-awareness, and single-robot serial policies.
- All five policies compile and emit deterministic actions on a current NavDP
  generated example.

Remaining work:

- Add a split runner that applies policies to every episode.
- Convert `BaselineAction` into evaluator/RL task actions.
- Add unit tests for policy ordering and tie-breaking.

Acceptance checks:

- Every baseline emits deterministic `BaselineAction` values.
- Pilot split can produce a comparative metrics table.

### GN-Bench-Tools: `GN_Bench/human_eval/rl_task.py`

Purpose: expose the benchmark as an RL-style task.

Work to do:

- Define observation contract.
- Define action contract.
- Convert evaluator metrics into reward.
- Bind to `EmbodiedTask` after deterministic replay works.

Acceptance checks:

- A scripted baseline can run reset/step without simulator rendering.
- Reward matches deterministic replay result for fixture trajectories.

### GN-Bench-Tools: Task And Measure Registration

Purpose: integrate human-centric metrics with GN-Bench task/config machinery.

Work to do:

- Add `GN_Bench/human_eval/task.py`.
- Register `HumanCentricTask-v0`.
- Implement `overwrite_sim_config` and episode-active logic.
- Add measure wrappers if needed by `Env.get_metrics()`.

Acceptance checks:

- GN-Bench can construct an `Env` with the human-centric task and dataset.
- `env.reset()` and one `env.step()` work on a fixture episode.

### GN-Bench-Tools: Simulator Integration

Purpose: eventually render/evaluate dynamic humans inside GN-Bench simulator.

Work to do:

- Identify actor sequence format consumed by `GNBenchSim.reconfigure`.
- Map NavDP human action sequence assets to simulator actor sequence dirs.
- Keep replay-only evaluation working without rendering.
- Add rendered-observation mode only after replay metrics are stable.

Acceptance checks:

- Replay-only evaluation works without rendering.
- A later smoke test can render one human actor sequence in one pilot scene.

### GN0: Documentation And Coordination

Purpose: keep cross-repo work synchronized while avoiding duplicated ownership.

Work to do:

- Track GN0/GN-Bench-Tools tasks here.
- Treat NavDP schema/datagen docs as producer-owned.
- Keep the consumer contract explicit and tolerant of additive producer fields.

Acceptance checks:

- A new contributor can find branch, repo ownership, MVP scope, and next GN0
  tasks from GN0 docs in under five minutes.

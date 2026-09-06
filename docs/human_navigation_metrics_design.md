# Human Navigation Metrics Design

Last updated: 2026-08-21

This document is the source of truth for GN0 human-centric navigation metrics.
Keep it in sync with:

- `GN-Bench-Tools/GN_Bench/human_eval/evaluator.py`
- `GN-Bench-Tools/GN_Bench/human_eval/social_metrics.py`
- `eval_navdp_missions.py`
- `vln_eval_results.py`
- `run_vln_native_eval.py`

Any code change that adds, removes, renames, or changes the semantics of a
reported metric should update this document in the same change.

## Design Goals

GN0 should report two compatible metric layers:

1. Standard VLN metrics so GN0 results remain comparable with R2R, VLN-CE,
   RxR/R4R, REVERIE-style, and related navigation papers.
2. Human-centric mission metrics that expose whether an agent handled identity,
   dynamic humans, social constraints, queues, multi-robot coordination, and
   mission timing.

The benchmark should avoid one opaque "score" during development. The top-line
score should be decomposable into observable failure modes:

- Did the robot reach the goal or target?
- Did it stop at the right time?
- Was the route efficient?
- Did it follow the intended path or only reach the endpoint?
- Did it respect humans, queues, groups, and dynamic obstacles?
- Did it satisfy mission release, priority, and deadline semantics?

## Current Implementation

Current deterministic replay emits `ReplayResult.metrics` plus per-mission
records in `ReplayResult.mission_results`.

Current model/result normalization emits `VLNEvaluationResult` rows. The
top-level row has coarse model-comparison fields:

- `episode_count`
- `total_missions`
- `total_events`
- `success_count`
- `mean_mission_success_rate`
- `mean_completion_rate`
- `metrics_json`

Publication replay also emits normalized JSONL/CSV rows through
`GN_Bench.human_eval.results`. Each row carries the Part 2 metric layer:
`navigation_error_m`, `success_rate`, `collision_rate`,
`total_collision_rate`, `mission_completion_rate`, `weighted_mission_score`,
`deadline_miss_rate`, `queue_order_violation_rate`,
`personal_space_violation_s`, `pedestrian_yield_violation_rate`,
`group_integrity_violation_rate`, `correct_human_fulfillment_rate`,
`multi_robot_throughput`, `handoff_success_rate`, and
`cancellation_compliance_rate`.

Rows are tagged with `publication_variants` so result tables can be grouped by
`human_free`, `human_present`, `social_law`, and `full_mission_stream`.
`eval_navdp_missions.py` writes these rows as `result_rows.jsonl` and
`result_rows.csv`; `summary.json` includes `by_split`, `by_mission_type`, and
`by_publication_variant` aggregates.

Native GN0 log import currently preserves common BAE/GN0 fields inside
`metrics_json`: `mean_success`, `mean_oracle_success`, `mean_spl`,
`mean_path_length`, and `mean_distance_to_goal`.

Important interpretation:

- `mission_success_rate` is the primary replay metric for generated NavDP
  mission artifacts.
- `completion_rate` is event-log completion coverage when completion events are
  present. It is not a replacement for mission success on families where success
  must be trajectory/metadata-derived.
- `expected_result_passed` is fixture-health metadata, not a model performance
  metric.
- Difficulty and recovery metrics are diagnostic by default. They should explain
  scenario hardness and intervention burden without changing the family success
  definition unless a family explicitly states otherwise.
- JSON policy replay currently evaluates assignment/action decisions over
  producer trajectories. Full VLN path metrics require simulator/native agent
  trajectories.

## Standard VLN Metrics

Use these metrics for model comparisons whenever a native or simulator-backed
agent trajectory is available.

| Metric | Direction | Definition | GN0 status |
| --- | --- | --- | --- |
| `path_length_m` / TL / PL | lower diagnostic | Total distance traveled by the agent. | Native GN0 log import reads `path_length`; replay does not yet aggregate path length. |
| `navigation_error_m` / NE / DTG | lower | Final geodesic or navigable distance from stop position to goal. | Native GN0 log import reads `distance_to_goal`; replay has family-specific minimum/goal distances. |
| `oracle_navigation_error_m` / ONE | lower diagnostic | Minimum distance to goal at any point along the trajectory. | Not top-level yet. Derivable for simulator/native trajectories. |
| `success` / SR | higher | Episode success under the task stop criterion, usually final position within a goal radius. | Native logs read `success`; replay has mission-family `success`. |
| `oracle_success` / OSR | higher diagnostic | Whether the trajectory ever came within the success radius, independent of final stop. | Native GN0 log import reads `oracle_success`; not top-level in replay. |
| `spl` | higher | Success weighted by path efficiency: success times shortest-path length over max(shortest path, actual path). | Native GN0 log import reads `spl`; not available for artifact-only replay without native path lengths. |
| `ndtw` | higher | Normalized Dynamic Time Warping against a reference path; rewards path fidelity and order. | Planned for native/simulator trajectories with reference paths. |
| `sdtw` | higher | `success * ndtw`; combines endpoint success with trajectory fidelity. | Planned. |
| `cls` | higher | Coverage weighted by Length Score; rewards covering the reference path while penalizing wrong length. | Planned for instruction/path-fidelity reporting. |
| `steps_taken` | lower diagnostic | Number of actions or simulator steps. | Planned for native/simulator runs. |

Source notes:

- R2R introduced the core VLN setting and uses endpoint/goal-based navigation
  evaluation. See Anderson et al.,
  [Vision-and-Language Navigation](https://arxiv.org/abs/1711.07280).
- SPL comes from the embodied navigation evaluation recommendation paper by
  Anderson et al.,
  [On Evaluation of Embodied Navigation Agents](https://arxiv.org/abs/1807.06757).
- CLS was introduced for instruction/path fidelity in Jain et al.,
  [Stay on the Path](https://aclanthology.org/P19-1181/).
- nDTW and SDTW were introduced in Ilharco et al.,
  [General Evaluation for Instruction Conditioned Navigation using Dynamic Time Warping](https://arxiv.org/abs/1907.05446).
- VLN-CE commonly reports TL, NE, OS, SR, SPL, and nDTW. See the
  [VLN-CE repository](https://github.com/jacobkrantz/VLN-CE).
- REVERIE-style object grounding adds RGS/RGSPL. See the
  [REVERIE Challenge metrics](https://yuankaiqi.github.io/REVERIE_Challenge/challenge_2022.html).

## Standard Metric Policy For GN0

Use standard VLN metrics when the mission has a single navigational endpoint or
a clear per-robot endpoint. For multi-mission and multi-robot episodes:

- Compute path-level metrics per robot-leg or per mission-leg.
- Aggregate by mission first, then by episode, then by split.
- Do not let a single long multi-robot episode dominate the split mean because
  it has more trajectory samples.
- Always report the threshold used for success and social violations.

Top-level model comparison should eventually include:

- `mean_success_rate`
- `mean_spl`
- `mean_navigation_error_m`
- `mean_oracle_success_rate`
- `mean_ndtw`
- `mean_sdtw`
- `mean_mission_success_rate`
- `mean_social_violation_rate`
- `mean_deadline_success_rate`

Until the schema is widened, put new model-level aggregates inside
`VLNEvaluationResult.metrics_json`.

For the publication package, the stable replay summary keys are:

- `navigation_error_m`
- `success_rate`
- `collision_rate`
- `total_collision_rate`
- `mission_completion_rate`
- `weighted_mission_score`
- `deadline_miss_rate`
- `queue_order_violation_rate`
- `personal_space_violation_s`
- `pedestrian_yield_violation_rate`
- `group_integrity_violation_rate`
- `correct_human_fulfillment_rate`
- `multi_robot_throughput`
- `handoff_success_rate`
- `cancellation_compliance_rate`

## Cross-Mission GN0 Metrics

These apply to all human-centric families unless a family explicitly states
otherwise.

| Metric | Definition | Current code |
| --- | --- | --- |
| `mission_success_rate` | Mean of per-mission `success` values where success is defined. | Implemented in `HumanCentricEvaluator.replay`. |
| `mission_metric_count` | Number of missions with defined success metrics. | Implemented. |
| `mission_metric_success_count` | Number of successful missions with defined success metrics. | Implemented. |
| `deadline_success` / `*_deadline_success_count` | Mission finished by deadline. | Implemented per family where deadlines exist. |
| `collision_count` | Collision count from producer collision metadata or family check. | Implemented where available. |
| `duration_s` | Max timestamp seen in event/actor trajectories. | Implemented. |
| `assigned_mission_count` | Number of missions with assignment events. | Implemented. |
| `completed_mission_count` | Number of missions with completion events. | Implemented. |
| `completion_rate` | Completed mission events over mission count, only when completion replay exists. | Implemented. |
| `evidence` | Metric provenance: event log, trajectory, dense metadata, etc. | Implemented per mission result. |

## Social And Human-Safety Metrics

These are benchmark-facing when a mission has social rules and diagnostic when
the rule is not required by that family.

| Metric | Definition | Current status |
| --- | --- | --- |
| `minimum_non_target_human_distance_m` | Minimum robot distance to humans other than the target. | Implemented inline for delivery/social navigation. |
| `personal_space_violation_count` | Number of contiguous personal-space violations. | Implemented inline. |
| `personal_space_violation_duration_s` | Time spent inside personal-space threshold. | Implemented inline. |
| `wrong_human_contact_count` | Physical contact with non-target humans. | Implemented for delivery. |
| `pedestrian_yield_respected` | Whether robot yielded at a pedestrian conflict point. | Implemented inline for L2 social navigation. |
| `group_integrity_respected` | Whether robot avoided protected group regions. | Implemented inline for L3 social navigation. |
| `queue_order_respected` | Whether robot served/approached queue endpoints in allowed order. | Implemented inline for L4 social navigation. |
| `human_human_collision_free` | Dense-human clearance among humans. | Implemented for dense families. |
| `dense_robot_human_clearance_policy_respected` | No checked collision and no nominal robot-human conflicts. | Implemented for dense human/combined. |
| `robot_robot_clearance_policy_respected` | No robot-robot collision and minimum robot-robot distance respected. | Implemented for dense multi-robot/combined. |

The placeholder classes in `GN-Bench-Tools/GN_Bench/human_eval/social_metrics.py`
should become reusable implementations of the currently inline evaluator logic:

- `HumanDistanceMetrics`
- `FFormationMetrics`
- `QueueMetrics`
- `PedestrianFlowMetrics`
- `VulnerableHumanMetrics`

## Difficulty Metrics

Difficulty metrics describe the scenario, not the agent. They are useful for
split balancing, failure analysis, curriculum learning, and reward weighting,
but they should not replace success, collision, deadline, or social-law checks.

### Human Identification Difficulty

Use this shared component whenever a mission depends on choosing the correct
human: delivery, guidance, queue service, escort, rendezvous, implicit need
fulfillment, group interviews, or any future family with `target_human_id`,
`informant_human_id`, `active_human_ids`, or equivalent target fields.

V0 can use human asset metadata as a proxy so the evaluator does not depend on a
separate image-embedding data-processing pipeline. Later rendered visual
similarity from finalized human crops can replace or calibrate the asset proxy.

Recommended raw per-distractor value:

```text
s_i = identity_similarity(target, human_i) * exposure_i
```

Where `identity_similarity` is computed from available asset or descriptor
metadata in v0, such as avatar id, clothing template/color, hair asset, body
shape bucket, role, action, and carried item. `exposure_i` should stay separate
from visual identity and represent whether the distractor is task-relevant:
near the target, near the robot path, co-visible, or likely to be encountered.

Use group statistics rather than only the single closest pair:

```text
s_max = max_i(s_i)
s_top3 = mean(top_3(s_i))
confuser_mass = log(1 + count(s_i >= threshold)) / log(1 + num_distractors)

raw = 0.55 * s_max + 0.30 * s_top3 + 0.15 * confuser_mass
```

Map `raw` into `[0, 1]` with a normalized sigmoid so easy cases stay near zero
and difficulty increases sharply after a confusability threshold:

```text
difficulty =
  (sigmoid(k * (raw - midpoint)) - sigmoid(k * (0 - midpoint)))
  / (sigmoid(k * (1 - midpoint)) - sigmoid(k * (0 - midpoint)))
```

Suggested initial parameters: `threshold = 0.70`, `midpoint = 0.55`, `k = 8.0`.
These are tuning defaults, not a permanent benchmark contract.

Recommended shared metric keys:

- `human_identification_difficulty`
- `human_identification_best_confuser_id`
- `human_identification_best_confuser_similarity`
- `human_identification_top3_confuser_similarity`
- `human_identification_confuser_count`
- `human_identification_similarity_source`

Mission-specific aliases may copy these values for readability, for example
`deliver_to_human_target_identification_difficulty`.

## Dense Collision-Avoidance And Recovery Policy

Dense human and multi-robot families should follow the common collision-avoidance
benchmark shape for top-line reporting:

```text
strict_success =
  active_robot_goal_success
  AND collision_free
  AND clearance_policy_respected
  AND deadline_success, if a deadline exists
```

For simulator or native-agent rollouts, recovery/intervention metrics should be
raw counters first. Do not bake a weighted recovery score into the evaluator
until reporting needs prove it is useful.

Recommended recovery counters:

- `stuck_recovery_count`
- `collision_recovery_count`
- `deadlock_recovery_count`
- `safe_reposition_count`
- `teleport_recovery_count`
- `local_replan_recovery_count`
- `total_recovery_count`
- `intervention_free_success`

`total_recovery_count` should be the sum of the category counts. Paper-facing
reports may later combine or threshold these counters, but evaluator outputs
should preserve the raw categories.

## Mission Family Metrics

### `deliver_to_human`

Question answered: Did the agent identify the right person, approach safely, and
complete the delivery before the deadline?

Benchmark-facing metrics:

- `deliver_to_human_success_count`
- `correct_human_reached_count`
- `object_delivered_count`
- `deadline_success_count`
- `wrong_human_contact_count`
- `personal_space_violation_count`
- `personal_space_violation_duration_s`
- `target_min_distance_m`
- `target_contact_time_s`
- `human_identification_difficulty`
- `deliver_to_human_target_identification_difficulty`
- `human_identification_best_confuser_id`
- `human_identification_confuser_count`

Design notes:

- Target contact uses the mission contact threshold.
- Non-target human contact is treated as a fatal physical-clearance violation.
- Personal-space buffer violations are reported even when not fatal, so reports
  can distinguish "completed, but socially poor" from "failed delivery".
- Target-identification difficulty is diagnostic. V0 should use group-level
  human asset/descriptor confusability; later rendered visual similarity can
  replace the asset proxy.
- Future native runs should also report standard VLN `navigation_error_m`,
  `spl`, and `oracle_success` to the target/contact region.

### `navigate_with_social_constraints`

Question answered: Did the agent reach the navigation goal while satisfying the
active social law set?

Benchmark-facing metrics:

- `navigate_with_social_constraints_success_count`
- `social_navigation_goal_reached_count`
- `social_navigation_deadline_success_count`
- `social_navigation_collision_count`
- `social_navigation_social_law_success_count`
- `social_navigation_personal_space_violation_count`
- `social_navigation_personal_space_violation_duration_s`
- `pedestrian_yield_success_count`
- `pedestrian_yield_violation_count`
- `group_integrity_success_count`
- `group_region_violation_count`
- `group_region_violation_duration_s`
- `queue_order_success_count`
- `queue_order_violation_count`

Law-specific logic:

- L1 personal space: no violations against task-relevant humans outside allowed
  contact roles.
- L2 pedestrian yield: preserve right-of-way at conflict points with sufficient
  time gap and distance.
- L3 group integrity: avoid protected group-center regions/capsules.
- L4 queue order: approach queue tail/service points without cutting.

Future additions:

- Add near-miss severity buckets.
- Add vulnerable-human larger-buffer weighting when roles indicate children,
  elderly, disabled, or medically vulnerable people.
- Add path-fidelity metrics when a reference route is semantically meaningful.

### `human_guided_uncertain_region`

Question answered: Did the agent recognize uncertainty, ask the right human,
wait for guidance, resolve the target, and complete the clarified navigation?

Benchmark-facing metrics:

- `human_guided_uncertain_region_success_count`
- `guidance_requested_count`
- `human_guidance_received_count`
- `uncertainty_resolved_count`
- `resolved_target_reached_count`
- `guidance_stop_verified_count`
- `goal_reach_time_s`
- `minimum_goal_distance_m`
- `deadline_success`
- `collision_count`

Design notes:

- Request/response/resolution are event-log obligations.
- Resolved-target reach is trajectory-derived.
- Stop-for-guidance is a social/interaction quality requirement when the mission
  specifies that the robot should stop instead of continuing through uncertainty.
- If the mission requires identifying a specific informant or resolved human
  target, report the shared `human_identification_*` difficulty metrics.

Future additions:

- Guidance latency: `guidance_response_time_s - guidance_request_time_s`.
- Excess asking count and wrong-informant count.
- Resolution quality when multiple candidate targets remain.

### `serve_queue`

Question answered: Did the agent serve the right person at the right time
without skipping earlier queue members?

Benchmark-facing metrics:

- `serve_queue_success_count`
- `serve_queue_correct_human_reached_count`
- `serve_queue_nearest_contact_reached_count`
- `serve_queue_previous_complete_count`
- `serve_queue_order_preserved_count`
- `target_contact_time_s`
- `target_min_distance_m`
- `queue_index`
- `queue_order`
- `collision_count`
- `human_identification_difficulty`
- `serve_queue_target_identification_difficulty`
- `human_identification_best_confuser_id`
- `human_identification_confuser_count`

Design notes:

- Correct contact is evaluated after mission release and before deadline.
- Previous queue members must already be complete before serving the current
  target.
- Queue order is currently checked from declared mission metadata and event
  order; simulator-native runs should also detect physical queue cutting.
- If service depends on identifying the correct queue member, report the shared
  `human_identification_*` difficulty metrics plus the
  `serve_queue_target_identification_difficulty` alias.

Future additions:

- Service latency by queue index.
- Fairness/starvation metrics over long queues.
- Queue segmentation and cutting traces from `QueueMetrics`.

### `mission_stream`

Question answered: Did the agent handle a released sequence of child missions
with correct assignment, timing, priority, terminal goals, and parent completion?

Benchmark-facing metrics:

- `mission_stream_parent_success_count`
- `mission_stream_child_success_count`
- `mission_stream_child_goal_reached_count`
- `mission_stream_child_timing_success_count`
- `mission_stream_child_eos_count`
- `mission_stream_parent_terminal_goal_success_count`
- `mission_stream_priority_order_success_count`
- `mission_stream_released_children_completed_count`
- `released_child_mission_count`
- `assigned_child_mission_count`
- `completed_child_mission_count`
- `eos_child_mission_count`

Design notes:

- Parent success is an orchestration metric; child success is a mission-leg
  metric.
- Priority order is enforced through child timing and dispatch record checks.
- Terminal goals verify that the parent stream ends with robots in the expected
  locations, not just that event logs are complete.
- `robot_eos` is the robot end-of-sequence event for a child mission leg. It
  closes out the child leg after completion and verifies the stream has reached
  the expected handoff or terminal state.

Future additions:

- Backlog size over time.
- Reassignment churn.
- Missed-release latency and priority-inversion duration.

### `dense_dynamic_humans`

Question answered: Did active robots reach goals while avoiding robot-human
collisions and respecting required clearance?

Benchmark-facing core metrics:

- `dense_dynamic_humans_success_count`
- `dense_active_robot_goal_success_count`
- `dense_robot_human_clearance_success_count`
- `all_active_robot_goal_regions_reached`
- `collision_count`
- `collision_free`
- `minimum_clearance_m`
- `required_clearance_m`

Diagnostic metrics:

- `dense_humans_keep_moving_success_count`
- `dense_human_human_collision_free_count`
- `dense_robot_wait_violation_count`
- `dense_nominal_robot_human_conflict_count`
- `dense_corner_case_recovery_count`
- `stuck_recovery_count`
- `collision_recovery_count`
- `safe_reposition_count`
- `teleport_recovery_count`
- `total_recovery_count`
- `intervention_free_success`

Design notes:

- Producer collision metadata is the primary robot-human clearance contract.
- Nominal robot-human conflict samples indicate unsafe dense interactions even
  when no collision is declared.
- Recovery counts are reported as intervention burden. They are not fatal by
  themselves unless the strict success conditions fail.

Future additions:

- Near-miss severity distribution.
- Human comfort score based on minimum distance and relative speed.
- Robot freezing/oscillation duration.

### `dense_multi_robot`

Question answered: Did all active robots reach their goals while avoiding
robot-robot collisions and respecting multi-robot spacing?

Benchmark-facing core metrics:

- `dense_multi_robot_success_count`
- `dense_multi_active_robot_goal_success_count`
- `dense_multi_robot_robot_collision_free_count`
- `dense_multi_robot_clearance_success_count`
- `minimum_robot_robot_distance_m`
- `minimum_required_robot_robot_distance_m`
- `minimum_robot_robot_clearance_m`
- `closest_robot_pair`

Diagnostic metrics:

- `dense_multi_robot_wait_count`
- `dense_multi_robot_wait_violation_count`
- `dense_multi_corner_case_recovery_count`
- `dense_multi_robot_robot_deadlock_recovery_count`
- `stuck_recovery_count`
- `collision_recovery_count`
- `deadlock_recovery_count`
- `safe_reposition_count`
- `teleport_recovery_count`
- `total_recovery_count`
- `intervention_free_success`

Design notes:

- Robot-robot clearance uses checked collision metadata when the closest pair is
  robot-robot and falls back to trajectory sampling otherwise.
- Stops/waits are valid when mission metadata declares required stops or when
  blockers explain the wait.
- Deadlock and reposition recoveries should be counted separately from strict
  collision avoidance.

Future additions:

- Deadlock duration.
- Per-robot path inefficiency and workload balance.
- Coordination overhead: waiting/turning/gliding per completed robot goal.

### `dense_dynamic_combined`

Question answered: Did the system handle robot-human and robot-robot
collision-avoidance constraints at the same time?

Benchmark-facing core metrics:

- `dense_dynamic_combined_success_count`
- `dense_combined_active_robot_goal_success_count`
- `dense_combined_robot_human_clearance_success_count`
- `dense_combined_robot_robot_collision_free_count`
- `dense_combined_robot_robot_clearance_success_count`

Diagnostic metrics:

- `dense_combined_humans_keep_moving_success_count`
- `dense_combined_human_human_collision_free_count`
- `dense_combined_robot_wait_violation_count`
- `dense_combined_nominal_robot_human_conflict_count`
- `dense_combined_corner_case_recovery_count`
- `dense_combined_robot_robot_deadlock_recovery_count`
- `stuck_recovery_count`
- `collision_recovery_count`
- `deadlock_recovery_count`
- `safe_reposition_count`
- `teleport_recovery_count`
- `total_recovery_count`
- `intervention_free_success`

Design notes:

- Combined strict success is conjunctive: robot goals, robot-human collision
  avoidance, robot-robot collision avoidance, required clearance, and deadline
  success if present.
- Combined metrics should remain decomposed. A failure report must indicate
  which sub-system failed, not just that the combined episode failed.
- Human-human activity/clearance, waits, deadlocks, and recoveries are
  diagnostics unless the benchmark configuration explicitly promotes them to
  success conditions.

Future additions:

- Interaction attribution: robot-human, robot-robot, or human-human root cause.
- Aggregate social burden: how much robot behavior disturbed human flow.

## Result Reporting Design

Reports should have three levels:

1. Model-level row: one row per model/run/split in `VLNEvaluationResult`.
2. Episode-level row: one row per scenario with aggregate mission, VLN, and
   social metrics.
3. Mission-level row: one row per mission with family-specific metrics and
   violation traces.

Recommended report groups:

- `navigation`: SR, SPL, NE, OSR, path length, nDTW, SDTW, CLS.
- `mission`: mission success, deadline success, assignment coverage, completion.
- `human_safety`: collisions, near misses, personal-space and clearance.
- `social_laws`: yield, group, queue, vulnerable-human metrics.
- `coordination`: multi-robot spacing, wait/deadlock/reassignment metrics.
- `difficulty`: human-identification, density, clearance, and deadline pressure.
- `recovery`: stuck, collision, deadlock, reposition, teleport, and replan
  counters.
- `debug`: evidence source, thresholds, closest actors, trace IDs.

## Implementation Roadmap

1. Add violation traces to `ReplayResult` or mission results.
   - Minimal trace fields: `metric_name`, `actor_ids`, `mission_id`,
     `start_time_s`, `end_time_s`, `min_distance_m`, `threshold_m`,
     `sample_indices`, and `explanation`.
2. Move reusable social checks from `HumanCentricEvaluator` into
   `social_metrics.py` without changing output keys.
3. Add shared human-identification difficulty helpers with asset/descriptor
   proxy scoring first and rendered visual similarity as a later source.
4. Add raw recovery counters for simulator/native dense rollouts without
   changing strict success semantics.
5. Add simulator/native path aggregates:
   - `path_length_m`
   - `navigation_error_m`
   - `oracle_navigation_error_m`
   - `oracle_success`
   - `spl`
   - `steps_taken`
6. Add path-fidelity metrics when reference paths are available:
   - `ndtw`
   - `sdtw`
   - `cls`
7. Widen `VLNEvaluationResult` only after native runs consistently emit the
   fields. Until then, preserve expanded metrics in `metrics_json`.
8. Add paper-facing summary export:
   - model table;
   - per-family table;
   - social violation table;
   - failure trace inventory.

## Open Design Questions

- Should combined mission success require zero social violations, or should
  social violations be reported separately with a graded social score?
- Should mission streams report parent success as one mission or weight by child
  mission count in model-level averages?
- Which recovery categories should appear in the first simulator/native dense
  rollout logs, and which should remain producer-side diagnostics?
- Should object/person grounding metrics mirror REVERIE RGS/RGSPL for future
  object-target and human-identification families?
- What is the canonical shortest-path source for SPL in dynamic-human scenes:
  static navmesh, time-expanded planner, or producer planned route?

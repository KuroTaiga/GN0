# Human Eval Mission Family Progress

Created: 2026-07-28

## Repo Context

- GN0 repo: `/Users/dongjk/ProjectFiles/GN0`
- Current branch: `dynamic-human-benchmark-implementation`
- Local state when this tracker was created: `.gitmodules`, `GN-Bench-Tools`, and `docs/` already had uncommitted or untracked changes. Do not revert unrelated work.
- Rule: implement, test, and mark progress for exactly one mission family at a time.
- Default dependency order:
  1. `deliver_to_human`
  2. `navigate_with_social_constraints`
  3. `human_guided_uncertain_region`
  4. `serve_queue`
  5. `mission_stream`
  6. `dense_dynamic_humans`
  7. `dense_multi_robot`
  8. `dense_dynamic_combined`

## Source Of Truth

- NavDP demo manifest:
  `/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/configs/benchmark/human_centric_mission_stream/demo_scene_manifest.json`
- GN0 implementation areas:
  - `GN-Bench-Tools/GN_Bench/human_eval/`
  - `GN-Bench-Tools/GN_Bench_baselines/human_eval/`

## Progress Checklist

Status values: `Not Started`, `In Progress`, `Complete`.

Do not mark a mission family `Complete` until its row names the focused tests that passed. Keep exactly one row marked `In Progress`.

| Status | Mission family | NavDP sample checked | Adapter support | Evaluator metrics | Policy behavior | RL observation/reward | Tests | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| In Progress | `deliver_to_human` | Checked `/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples/deliver_to_human/jsons/example_CHINGMU_rescaled_1_0001_858833_deliver_to_human.json` on 2026-07-28 | Raw payload load only. Need normalized target human, target pose, assignment, deadline, and success-condition fields. | Not implemented. Need deterministic checks for correct target reach, object delivery, personal-space handling, deadline, and no wrong-human completion. | Existing baselines can emit assignment actions and resolve target human pose. Need route metadata only if evaluator requires it. | Not implemented. Add observation/reward fields only after evaluator metrics exist. | Pending: add focused `deliver_to_human` adapter/evaluator tests before completion. | First family establishes shared helpers for target pose, target human lookup, deadline, assignment, and completion checks. |
| Not Started | `navigate_with_social_constraints` | Pending | Blocked until `deliver_to_human` completes. | Blocked | Blocked | Blocked | Pending | Next after `deliver_to_human`; expected to reuse target/pose helpers and add social-structure constraints. |
| Not Started | `human_guided_uncertain_region` | Pending | Blocked until prior families complete. | Blocked | Blocked | Blocked | Pending | Dependency order places this before `serve_queue` even though the manifest lists `serve_queue` earlier. |
| Not Started | `serve_queue` | Pending | Blocked until prior families complete. | Blocked | Blocked | Blocked | Pending | Queue order, service point, and served-human trace metrics should be introduced here. |
| Not Started | `mission_stream` | Pending | Blocked until prior families complete. | Blocked | Blocked | Blocked | Pending | Multi-mission and multi-robot stream support should build on completed single-family contracts. |
| Not Started | `dense_dynamic_humans` | Pending | Blocked until prior families complete. | Blocked | Blocked | Blocked | Pending | Dynamic-human collision, near-miss, and yielding metrics belong here unless introduced earlier by a checked sample. |
| Not Started | `dense_multi_robot` | Pending | Blocked until prior families complete. | Blocked | Blocked | Blocked | Pending | Multi-robot goal completion and robot-robot interaction metrics belong here. |
| Not Started | `dense_dynamic_combined` | Pending | Blocked until prior families complete. | Blocked | Blocked | Blocked | Pending | Final combined dense case should only start after dynamic-human and dense-multi-robot contracts are tested. |

## Per-Family Workflow

Before moving to the next mission family:

1. Inspect one real NavDP generated scenario JSON for the selected family.
2. Record mission-specific fields and success conditions in this tracker.
3. Implement adapter normalization for that family.
4. Implement deterministic evaluator support for its success conditions.
5. Update baseline policy behavior only where the mission requires different assignment or routing metadata.
6. Add RL observation/reward fields only after evaluator metrics exist.
7. Add focused tests using a fixture or copied minimal JSON payload.
8. Mark the family `Complete` only when tests pass, then add a dated handoff note.

## Current Working Family

- Selected mission family: `deliver_to_human`
- Source sample path:
  `/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples/deliver_to_human/jsons/example_CHINGMU_rescaled_1_0001_858833_deliver_to_human.json`
- Source sample summary:
  - `scenario_id`: `example_CHINGMU_rescaled_1_0001_858833_deliver_to_human`
  - `scene_id`: `0001_858833`
  - `schema_version`: `0.1`
  - One robot: `robot_alpha`
  - Humans: `human_target` with role `target_person`; `human_context` with role `bystander`
  - One mission: `mission_deliver_to_human_001`
- Expected schema fields:
  - Top level: `schema_version`, `scenario_id`, `scene_id`, `scene_assets`, `robots`, `humans`, `missions`, `social_structures`, `event_log`, `expected_result`, `metadata`
  - Mission fields: `mission_id`, `mission_type`, `assigned_robot_id`, `release_time`, `deadline`, `priority`, `target_human_id`, `target_object_id`, `target_region_id`, `social_law_ids`, `success_conditions`, `metadata`
  - Mission metadata fields seen in the sample: `contact_distance_m`, `planned_goal_world`, `target_human_world`, `mission_end_time_s`, `endpoint_semantics`, `avoidance_semantics`, `target_human_description`, `target_human_resource_id`, `target_object_grounding`, `robot_instructions`, `human_behavior_instructions`
  - Success conditions seen in the sample: `correct_human_reached`, `object_delivered`, `personal_space_respected`
- Implementation goal:
  Normalize enough mission, human, robot, deadline, target pose, and success-condition data for deterministic `deliver_to_human` replay metrics. Then expose those metrics to RL reward code.
- Open questions:
  - Should `object_delivered` be inferred solely from reaching `target_human_id` within `contact_distance_m`, or should the evaluator require an explicit delivery event when NavDP emits one?
  - Should `personal_space_respected` exempt the target human inside `contact_distance_m` for the full approach or only at terminal contact?
  - Should deadline success use `deadline` or `metadata.mission_end_time_s` when both are present and differ?
- Next command to run:
  `python3 -m py_compile GN-Bench-Tools/GN_Bench/human_eval/scenario_adapter.py GN-Bench-Tools/GN_Bench/human_eval/evaluator.py GN-Bench-Tools/GN_Bench/human_eval/rl_task.py GN-Bench-Tools/GN_Bench_baselines/human_eval/policies.py`

## Remote Lab Notes

- Full GN0/BAE InteriorGS evaluation should run on a Linux NVIDIA CUDA machine. The documented install path uses PyTorch CUDA 12.8 and CUDA extension builds for `diff-gaussian-rasterization`, `simple-knn`, and `fused-ssim`.
- Apple Silicon is useful only for lightweight Python work: docs, scenario JSON inspection, adapter/evaluator unit tests, and JSON-level baseline-policy smoke checks. It is not a practical target for full 3DGS rendering plus BAE inference without porting multiple CUDA-dependent layers.
- The standard evaluation path is headless. It does not launch a live simulator GUI. The simulator renders observations for the agent, and `BAEAgentBase.save_observation_images` writes per-step PNG artifacts under the result directory.
- Visual artifacts during a run are expected under paths like `tmp/<run>/<episode_id>/image/rgb/`, `tmp/<run>/<episode_id>/image/occ_traj/`, `tmp/<run>/<episode_id>/image/bev_traj/`, `tmp/<run>/<episode_id>/image/hist/`, and `tmp/<run>/<episode_id>/image/action/`.
- For remote viewing, run a simple HTTP server from the result directory and forward the port over SSH, for example:
  `python3 -m http.server 8000 --bind 127.0.0.1`
  then from the local machine:
  `ssh -L 8000:127.0.0.1:8000 user@remote-host`

## Session Handoff Log

### 2026-07-28

- Created this tracker from the one-mission-family plan.
- Verified NavDP demo manifest has all eight families: `deliver_to_human`, `navigate_with_social_constraints`, `serve_queue`, `mission_stream`, `human_guided_uncertain_region`, `dense_dynamic_humans`, `dense_multi_robot`, `dense_dynamic_combined`.
- Chose `deliver_to_human` as the only active family because it is first in dependency order.
- Sampled `/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples/deliver_to_human/jsons/example_CHINGMU_rescaled_1_0001_858833_deliver_to_human.json` and recorded target, deadline, assignment, contact, and success-condition fields above.
- No adapter, evaluator, policy, RL, or test implementation changes were made in this tracker-creation pass.

### 2026-07-29

- Added remote-machine handoff notes: use Linux NVIDIA CUDA for full GN0/BAE evaluation; Apple Silicon is only realistic for pure-Python scaffold work.
- Recorded that the lab is headless by default. It saves visual PNG artifacts under each result episode instead of opening a live GUI.
- Verified the current human-eval Python scaffold compiles when bytecode output is redirected away from Apple Python's default cache path:
  `PYTHONPYCACHEPREFIX=/private/tmp/gn0_pycache python3 -m py_compile GN-Bench-Tools/GN_Bench/human_eval/scenario_adapter.py GN-Bench-Tools/GN_Bench/human_eval/evaluator.py GN-Bench-Tools/GN_Bench/human_eval/rl_task.py GN-Bench-Tools/GN_Bench_baselines/human_eval/policies.py`
- Verified the JSON-level `OracleHumanCentricPolicy` smoke path emits an assignment for `robot_alpha` to `mission_deliver_to_human_001` on the sampled `deliver_to_human` scenario.
- Next implementation session should continue with `deliver_to_human` only: adapter normalization first, deterministic evaluator metrics second, RL observation/reward third, then focused tests before marking the family complete.

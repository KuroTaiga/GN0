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

Do not mark a mission family `Complete` until its row names the focused tests that passed. Keep exactly one row marked `In Progress` while unfinished families remain.

| Status | Mission family | NavDP sample checked | Adapter support | Evaluator metrics | Policy behavior | RL observation/reward | Tests | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Complete | `deliver_to_human` | Checked `/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples/deliver_to_human/jsons/example_CHINGMU_rescaled_1_0001_858833_deliver_to_human.json` on 2026-08-05 | GN-Bench `HumanCentricEpisode` support exists, including raw payload, scene id, start pose, `ref_json`, and `info["human_scenario"]`. | Implemented trajectory-derived checks for correct human reached, object delivered, deadline success, wrong-human physical contact, non-target minimum distance, and personal-space violation count/duration reporting. | JSON assignment sweep covers all five baseline policies; simulator-backed rollout remains pending. | Deferred to RL task phase; evaluation-phase completion does not require reward mapping. | Passing: `python3 -m unittest tests.test_human_eval_navdp_bridge`; real sample passes via `eval_navdp_missions.py --source ...deliver_to_human.json`. | Mission-stream child delivery tasks use stream-specific planned-goal/EOS contracts because their route targets differ from the single-family contact contract. Delivery reports personal-space buffer violations but uses physical non-target contact as the fatal avoidance condition. |
| Complete | `navigate_with_social_constraints` | Checked L1/L2/L3/L4 samples under `/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples/navigate_with_social_constraints/` on 2026-08-05 | GN-Bench `HumanCentricEpisode` support works for all four social-law cases. | Implemented trajectory-derived goal/deadline/collision checks plus L1 personal-space, L2 pedestrian-yield conflict timing, L3 group-region capsule clearance, and L4 queue-tail endpoint checks. | JSON assignment sweep covers all five baseline policies. | Deferred to RL task phase. | Passing: `python3 -m unittest tests.test_human_eval_navdp_bridge`; real 20-file social-navigation directory passes through `eval_navdp_missions.py`. | Uses NavDP checked collision metadata when available; L3 allows 0.05 m route discretization tolerance around the group law region. |
| Complete | `human_guided_uncertain_region` | Checked `/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples/human_guided_uncertain_region/jsons/example_InteriorGS_0732_841582_human_guided_uncertain_region.json` on 2026-08-05 | GN-Bench `HumanCentricEpisode` support works for the family. | Implemented trajectory/event checks for guidance request, human response, uncertainty resolution, stop-for-guidance interval, resolved-target reach, deadline success, and checked collision count. | JSON assignment sweep covers all five baseline policies. | Deferred to RL task phase. | Passing: `python3 -m unittest tests.test_human_eval_navdp_bridge`; real 5-file human-guided directory passes through `eval_navdp_missions.py`. | Evaluation now uses `trajectory_human_guided_uncertain_region` evidence instead of generic completion-only evidence. |
| Complete | `serve_queue` | Checked `/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples/serve_queue/jsons/example_CHINGMU_rescaled_3_0011_859081_serve_queue.json` on 2026-08-05 | GN-Bench `HumanCentricEpisode` support works for multi-mission queue scenarios. | Implemented target-human contact after mission release, nearest queue contact, previous queue completion, declared queue-order preservation, deadline success, and checked collision count. | JSON assignment sweep covers all five baseline policies. | Deferred to RL task phase. | Passing: `python3 -m unittest tests.test_human_eval_navdp_bridge`; real 5-file queue directory passes through `eval_navdp_missions.py`. | Handles ordered service legs with per-target contact points and event-backed previous-completion checks. |
| Complete | `mission_stream` | Checked `/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples/mission_stream/jsons/example_InteriorGS_0732_841582_mission_stream.json` on 2026-08-05 | GN-Bench `HumanCentricEpisode` support loads parent and child missions. | Implemented trajectory/timing checks for parent child coverage, release/assignment/completion/EOS timing, priority-order metadata consistency, per-child planned-goal reach, parent terminal robot goals, deadline success, and checked collision count. | JSON assignment sweep covers all five baseline policies. | Deferred to RL task phase. | Passing: `python3 -m unittest tests.test_human_eval_navdp_bridge`; real 5-file mission-stream directory passes through `eval_navdp_missions.py`. | Stream child delivery/navigation uses stream-specific planned-goal/EOS contracts because child route targets differ from single-family target-contact/social-law schemas. |
| Complete | `dense_dynamic_humans` | Checked `/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples/dense_dynamic_humans/jsons/example_CHINGMU_rescaled_2_0063_859024_dense_dynamic_humans.json` on 2026-08-05 | GN-Bench `HumanCentricEpisode` support loads dense moving-human scenarios. | Implemented trajectory/metadata checks for active robot goal reach, checked collision, nominal robot-human conflict counts, moving-human activity through robot completion, human-human clearance, blocked-wait policy, and corner-case recovery counts. | JSON assignment sweep covers all five baseline policies. | Deferred to RL task phase. | Passing: `python3 -m unittest tests.test_human_eval_navdp_bridge`; real 5-file dense-dynamic-human directory passes through `eval_navdp_missions.py`. | Uses producer checked collision and nominal conflict metadata as the primary robot-human clearance contract; raw corner-case recoveries are reported but not fatal. |
| Complete | `dense_multi_robot` | Checked `/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples/dense_multi_robot/jsons/example_CHINGMU_rescaled_2_0063_859024_dense_multi_robot.json` on 2026-08-05 | GN-Bench `HumanCentricEpisode` support loads dense multi-robot scenarios and skips `_cornercase_metadata` sidecars. | Implemented trajectory/metadata checks for all active robot goal reach, checked robot-robot collision, minimum robot-robot distance, dense motion/wait reporting, deadline success, and corner-case recovery counts. | JSON assignment sweep covers all five baseline policies. | Deferred to RL task phase. | Passing: `python3 -m unittest tests.test_human_eval_navdp_bridge`; real 5-file dense-multi-robot directory passes through `eval_navdp_missions.py`. | Multi-robot waits are valid when the producer declares required stops; robot-robot deadlock recoveries are reported but not fatal. |
| Complete | `dense_dynamic_combined` | Checked `/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples/dense_dynamic_combined/jsons/example_CHINGMU_rescaled_2_0063_859024_dense_dynamic_combined.json` on 2026-08-05 | GN-Bench `HumanCentricEpisode` support loads combined dense scenarios and skips `_cornercase_metadata` sidecars. | Implemented composed dense human plus dense multi-robot evaluator metrics: active robot goals, checked collision, nominal robot-human conflicts, human activity, human-human clearance, robot-robot clearance, wait/recovery reporting, and deadline success. | JSON assignment sweep covers all five baseline policies. | Deferred to RL task phase. | Passing: `python3 -m unittest tests.test_human_eval_navdp_bridge`; real 5-file dense-dynamic-combined directory passes through `eval_navdp_missions.py`. | Final combined dense evaluation contract is complete for replay-only JSON evaluation. |

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

- Selected mission family: none; all eight evaluation-phase mission families are complete.
- Source sample path:
  `/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples/dense_dynamic_combined/jsons/example_CHINGMU_rescaled_2_0063_859024_dense_dynamic_combined.json`
- Source sample summary:
  - `scenario_id`: `example_CHINGMU_rescaled_2_0063_859024_dense_dynamic_combined`
  - `scene_id`: `0063_859024`
  - `schema_version`: `0.1`
  - Four active robots: `robot_001` through `robot_004`
  - Six moving humans: `human_fast_01`, `human_slow_01`, `human_normal_01`, `human_fast_02`, `human_slow_02`, `human_normal_02`
  - One mission: `mission_dense_dynamic_combined_001`
  - Event log currently has only `mission_release` and `robot_assignment`; success must be trajectory/metadata-derived.
- Expected schema fields:
  - Top level: `schema_version`, `scenario_id`, `scene_id`, `scene_assets`, `robots`, `humans`, `missions`, `social_structures`, `event_log`, `expected_result`, `metadata`
  - Mission metadata fields seen in the sample: `active_robot_ids`, `active_robot_count`, `configured_dense_robot_count`, `planned_goal_world`, `planned_goal_world_by_robot`, `minimum_robot_robot_distance_m`, `minimum_moving_robot_human_distance_m`, `minimum_stopped_robot_human_distance_m`, `minimum_human_human_distance_m`, `mission_end_time_s`, `expected_robot_motion`, `stationary_robot_ids`, `training_robot_ids`
  - Top-level dense metadata fields seen in the sample: `metadata.collision_check`, `metadata.dense_dynamic_combined.agent_adjustments`, `metadata.dense_dynamic_combined.robot_adjustments`, `metadata.dense_dynamic_combined.human_adjustments`, `metadata.dense_dynamic_combined.nominal_robot_human_conflict_samples`, `metadata.dense_dynamic_combined.corner_case_recovery`
  - Success conditions seen in the sample: `all_active_robot_goal_regions_reached`, `robots_keep_moving_when_passable`, `wait_only_when_immediately_blocked`, `dense_robot_human_clearance_policy_respected`, `humans_keep_moving_until_robot_completion`, `human_human_collision_free`, `no_robot_robot_collision`
- Implementation goal:
  Complete for replay-only JSON evaluation. Replay-backed RL observation/action/reward support exists; remaining work is simulator/native VLN adapter integration, not mission-family replay support.
- Closed decisions:
  - Combined success shares dense multi-robot stop semantics when producer metadata declares required stops.
  - Corner-case recovery deadlock/teleport/human-stall events are reported as explicit producer-side recovery metrics and are not fatal by themselves.
  - Checked collision metadata remains the primary clearance contract; trajectory sampling is used as a robot-robot distance fallback when the checked closest pair is not robot-robot.
- Next command to run:
  `python3 eval_navdp_missions.py --source /Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples --result-path /private/tmp/gn0_navdp_all_mission_examples`

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

### 2026-08-05

- Added replay-only NavDP mission entry point:
  `python3 eval_navdp_missions.py --source /Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples/example_manifest.json --result-path tmp/navdp_human_eval`.
- Added `HumanCentric-v0` dataset registration and tests under
  `GN-Bench-Tools/tests/test_human_eval_navdp_bridge.py`.
- Implemented first `deliver_to_human` trajectory metrics in
  `GN_Bench/human_eval/evaluator.py`: target contact, delivery, deadline,
  wrong-human contact, non-target minimum distance, and personal-space
  violation count/duration.
- Verified the real `deliver_to_human` sample reports `mean_mission_success_rate`
  `1.0` even though its event log has no completion event.
- Verified the current NavDP mission-stream manifest reports 5 episodes, 50
  missions, 198 events, 5 successes, and `mean_mission_success_rate` `1.0`.
- Marked `deliver_to_human` complete for the evaluation phase. RL reward mapping
  is explicitly deferred to the RL task phase.
- Implemented first `navigate_with_social_constraints` L1 personal-space
  trajectory metrics and kept L2/L3/L4 on event-log success until their own
  law-specific contracts are implemented.
- Verified the 20-file social-navigation example directory reports 20
  successes, 20 missions, 76 events, and `mean_mission_success_rate` `1.0`.
- Added trajectory-backed L2/L3/L4 social-navigation contracts:
  pedestrian-yield conflict timing, group-region capsule clearance, and
  queue-tail endpoint checks. The real 20-file social-navigation directory
  still reports 20 successes, 20 missions, 76 events, and
  `mean_mission_success_rate` `1.0`.
- Added trajectory/event metrics for `human_guided_uncertain_region`:
  guidance request/response, uncertainty resolution, stop-for-guidance,
  resolved-target reach, deadline, and checked collision count. The real
  5-file human-guided directory reports 5 successes, 5 missions, 31 events,
  and `mean_mission_success_rate` `1.0`.
- Added trajectory/event metrics for `serve_queue`: target contact after
  release, nearest queue contact, previous queue completion, declared queue
  order, deadline, and checked collision count. The real 5-file queue
  directory reports 5 successes, 20 missions, 70 events, and
  `mean_mission_success_rate` `1.0`.
- Marked `navigate_with_social_constraints`, `human_guided_uncertain_region`,
  and `serve_queue` complete for the evaluation phase. `mission_stream` is now
  the active family.
- Added trajectory/timing metrics for `mission_stream`: parent child coverage,
  release/assignment/completion/EOS timing, per-child planned-goal reach,
  parent terminal robot goals, priority-order metadata consistency, deadline,
  and checked collision count. The real 5-file mission-stream directory reports
  5 successes, 50 missions, 198 events, and `mean_mission_success_rate` `1.0`
  with `trajectory_mission_stream_parent` and `trajectory_mission_stream_child`
  evidence.
- Marked `mission_stream` complete for the evaluation phase. The active family
  is now `dense_dynamic_humans`.
- Added trajectory/metadata metrics for `dense_dynamic_humans`: active robot
  goal reach, checked collision, nominal robot-human conflict counts,
  moving-human activity, human-human clearance, blocked-wait policy, deadline,
  and corner-case recovery counts. The real 5-file dense-dynamic-human
  directory reports 5 successes, 5 missions, 10 events, and
  `mean_mission_success_rate` `1.0`.
- Marked `dense_dynamic_humans` complete for the evaluation phase. The active
  family is now `dense_multi_robot`.
- Added trajectory/metadata metrics for `dense_multi_robot`: active robot goal
  reach, checked robot-robot collision, minimum robot-robot distance,
  wait/recovery reporting, deadline, and corner-case recovery counts. The real
  5-file dense-multi-robot directory reports 5 successes, 5 missions, 10 events,
  and `mean_mission_success_rate` `1.0`.
- Marked `dense_multi_robot` complete for the evaluation phase. The active
  family is now `dense_dynamic_combined`.
- Added composed trajectory/metadata metrics for `dense_dynamic_combined`:
  active robot goal reach, checked collision, nominal robot-human conflict
  counts, moving-human activity, human-human clearance, robot-robot clearance,
  wait/recovery reporting, deadline, and corner-case recovery counts. The real
  5-file dense-dynamic-combined directory reports 5 successes, 5 missions,
  10 events, and `mean_mission_success_rate` `1.0`.
- Marked `dense_dynamic_combined` complete for the evaluation phase. All eight
  NavDP mission families are now covered by replay-only JSON evaluation.
- Verified the full `/tmp/mission_examples` tree, excluding `_cornercase_metadata`
  sidecars, reports 55 episodes, 115 missions, 415 events, 55 successes, and
  `mean_mission_success_rate` `1.0`.
- Adjusted `deliver_to_human` success semantics to distinguish target-contact
  tolerance from non-target physical contact. Personal-space buffer violations
  remain reported, but producer-expected delivery variants pass when no
  non-target physical contact occurs.
- Added replay-backed `HumanCentricRLTask` observation/action/reward support.
  A baseline assignment action can now drive `reset()`/`step()` without simulator
  rendering, and terminal reward components are derived from deterministic replay
  metrics.
- Added dependency-gated `HumanCentricTask-v0` registration with replay helpers
  and simulator config mapping. Full `Env` reset/step remains pending until
  GN-Bench task dependencies such as `gymnasium` are installed in the run
  environment.
- Added `vln_eval_results.py` to normalize replay summaries, native GN0 outputs,
  and external-reported model rows into one result schema. Verified it imports
  the full NavDP example replay summary as a completed
  `human_eval_json_policies` result row.
- Added the `vln_adapters` base contract, `vln_adapter_registry.py`, and
  `run_vln_native_eval.py`. The dispatcher ran
  `human_eval_json_policies` over the full NavDP example directory and wrote a
  normalized `/private/tmp/gn0_native_dispatcher_replay/vln_result.json`.
- Updated `plan_vln_evaluations.py` so newer public-checkpoint candidates now
  receive concrete dispatcher commands while remaining marked
  `adapter_required` until their model-specific adapter modules and local
  checkpoints exist.
- Added GN0 native log import to `vln_eval_results.py` for BAE-style
  `log/*.json` result directories.
- Added non-runnable adapter stubs for FutureNav, AwareVLN, GA-VLN, and
  TIC-VLA. The readiness registry now distinguishes `stub` from
  `native_ready`, preventing placeholder adapters from becoming runnable just
  because a checkpoint path exists.
- Added `prepare_vln_checkpoints.py`; the current post-2025 native-runnable
  checkpoint plan reports four missing fetchable checkpoints: FutureNav,
  AwareVLN, GA-VLN, and TIC-VLA.
- Updated native Python adapter dispatch so future `native_ready` adapters write
  normalized `VLNEvaluationResult` rows to `vln_result.json` instead of an
  adapter-specific payload.
- Added `export_vln_adapter_inputs.py` and `vln_adapters/navdp_inputs.py` to
  produce compact per-mission records for model adapters. Verified the full
  NavDP example directory exports 115 mission inputs across 55 episodes, all
  eight mission families, 15 multi-robot missions, and zero missing instructions
  or goals.

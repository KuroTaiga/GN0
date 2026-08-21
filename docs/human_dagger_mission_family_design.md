# Human DAgger Mission-Family Design

Created: 2026-08-21

This document tracks the DAgger contract for the eight current human-centric
mission families. The implementation lives in
`GN-Bench-Tools/GN_Bench/human_eval/dagger/`.

## Scope

The current DAgger path is a metric-backed supervision layer. It consumes model
actions, observations, replay metrics, and optional rollout history, then emits
a model-neutral `HumanDaggerSample` plus model-specific rendered records.

This is not yet a simulator-native teacher. Low-level path/action oracles should
be added after native rollout and recovery hooks are connected.

## Family Matrix

| Mission family | Primary faults | Current oracle action | Recovery signal | Remaining work |
| --- | --- | --- | --- | --- |
| `deliver_to_human` | Missing/wrong target, ambiguity, unsafe approach, bad stop timing | `assign_mission` to the target human | Safe reposition for unsafe approach | Replace metadata-only human similarity with rendered-image similarity when available; attach path oracle. |
| `navigate_with_social_constraints` | Goal miss, L1 personal space, L2 yield, L3 group integrity, L4 queue order, collision/near miss | `set_subgoal` with social repair fault context | Safe reposition or collision recovery | Generate law-specific repair subgoals such as queue tail, yield wait point, and group-region detour. |
| `human_guided_uncertain_region` | Missing guidance request, wrong informant, wait violation, resolved target ignored | `interact` for guidance, `no_op` while waiting, then assignment/subgoal repair | Mostly no-op/wait; collision recovery if replay reports it | Add post-response route oracle to the resolved target. |
| `serve_queue` | Missing/wrong queue member, order violation, cutting, wait required | `no_op` until prior queue members finish, otherwise `assign_mission` | Wait or safe queue-tail reposition | Add queue-tail repair subgoal for social-law queue cases. |
| `mission_stream` | Priority inversion, missed release, wrong child assignment, missing EOS, terminal goal missed | `assign_mission` for dispatch, `robot_eos` for closeout | Diagnostic unless collision/recovery metrics are present | Sequence child-level DAgger samples into one stream-level record. |
| `dense_dynamic_humans` | Active robot goal miss, robot-human collision/clearance, human motion stall, stuck/freeze, recovery required | `set_subgoal` with active robot subgoals and recovery strategy | Stuck, safe reposition, teleport, collision counts | Wire live stuck/collision detection to simulator recovery events. |
| `dense_multi_robot` | Active robot goal miss, robot-robot collision/clearance, deadlock, starvation, stuck/freeze, recovery required | `set_subgoal` with active robot subgoals and recovery strategy | Stuck, safe reposition, teleport, collision counts | Promote per-robot priority/starvation events from diagnostics into rollout state. |
| `dense_dynamic_combined` | Combined dense human and robot faults, deadlock/starvation, stuck/freeze, recovery required | `set_subgoal` with active robot subgoals and recovery strategy | Stuck, safe reposition, teleport, collision counts | Split failures into per-robot, per-human, and per-pair records for debugging. |

## Implementation Anchors

- `family_specs.py`: inspectable family contracts for handlers, signals, oracle
  actions, recovery counts, and remaining work.
- `mission_handlers.py`: concrete validators and oracle-correction routing.
- `recovery.py`: normalized recovery count taxonomy:
  `stuck_recovery_count`, `safe_reposition_count`,
  `teleport_recovery_count`, `collision_recovery_count`.
- `collector.py`: rollout-facing `observe_step(...)` hook and mission-stream
  child routing.

## Next Implementation Step

The next code step is simulator integration:

1. Attach live stuck/collision/reposition events to `metrics_snapshot`.
2. Add per-robot dense recovery records instead of scenario-level counts only.
3. Add low-level oracle actions to `DaggerOracleCorrection.low_level_actions`.
4. Add model-family exporters once the target training schema for each model is
   fixed.

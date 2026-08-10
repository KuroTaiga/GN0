# Navigation Model Evaluation Research

Date: 2026-08-05

This note tracks which navigation models GN0 already evaluates, which existing
models still need evaluation, and which post-2025 models should be considered
for new additions.

## Cutoff Rule

For "new" additions, use a strict first-public-release cutoff:

- Eligible new model: first public paper/report/project/model release on or
  after 2026-01-01.
- Not counted as new: 2025 arXiv/preprint releases, even if accepted to an
  ICLR/ICRA/CVPR 2026 venue. These can still be legacy comparators.

This matters because several strong navigation models have 2026 conference
labels but 2025 public release dates.

## Current GN0 Evaluation Inventory

| Status | Model or policy | Evidence in this repo | Notes |
| --- | --- | --- | --- |
| Actively configured | GN-BAE | `README.md`, `eval_bae_InteriorGS.sh`, `VLN_CE/vlnce_baselines/config/baselines/bae_InteriorGS.yaml` | Current InteriorGS workflow is BAE-only. |
| Implemented as JSON-level human-centric baselines | `oracle_human_centric`, `greedy_nearest`, `priority_greedy`, `no_human_awareness`, `single_robot_serial` | `GN-Bench-Tools/GN_Bench_baselines/human_eval/policies.py` | Implemented policies, but not a full simulator/model evaluation pipeline yet. |
| Present as inherited/default config only | `CMAPolicy`, `PointNavResNetPolicy`, DD-PPO weights, ORB-SLAM2 | `VLN_CE/vlnce_baselines/config/default.py`, `GN-Bench-Tools/GN_Bench_baselines/config/default.py` | Present in config scaffolding, but no current GN0 evaluation script/config comparable to BAE. |
| Not present | Most recent VLA/VLN foundation navigation models | repo search | Needs adapters or external runners. |

## Existing Models That Still Need Evaluation

These are not "new" under the cutoff rule, but they should be evaluated or
explicitly marked out of scope because they are standard comparators.

| Priority | Model family | Why evaluate | Local integration note |
| --- | --- | --- | --- |
| P0 | Shortest-path/oracle and random agents | Sanity checks for metrics, splits, and failure accounting. | Should be added before learned-model comparisons. |
| P0 | CMA / Seq2Seq VLN-CE baselines | Official VLN-CE baseline lineage; current repo still carries `CMAPolicy` config defaults. | Need a GN0-compatible config and runner or an external-results import path. |
| P1 | Waypoint VLN-CE models | Strong historical continuous-navigation comparators; useful for separating instruction grounding from low-level control. | Need action-space compatibility audit. |
| P1 | Navid / Uni-NaVid / NaVILA-style video-VLM navigators | Representative video/VLM navigation baseline line before 2026. | Likely easiest to compare through external logs if code/checkpoints are not GN-Bench-native. |
| P1 | StreamVLN | ICRA 2026 venue but first public arXiv/project release was 2025-07, so classify as legacy comparator, not new. | Strong RGB-only VLN-CE comparator; may need external runner. |
| P1 | NavFoM | ICLR 2026 venue but first public arXiv release was 2025-09, so classify as legacy comparator, not new. | Strong cross-task/cross-embodiment comparator. |
| P1 | InternVLA-N1 / DualVLN / NavDP stack | Public tooling matured around InternNav, but first technical reports are 2025. | Useful because InternNav provides many baselines and benchmark tables. |
| P2 | VLFM and open-vocabulary ObjectNav agents | Useful for object-goal/search families even if not instruction-following VLN. | Only compare on object/search episodes, not all mission families. |
| P2 | UrbanVLA / CityWalker-style urban micromobility models | Relevant to social and long-horizon outdoor navigation, but not GN0 indoor InteriorGS by default. | Keep as optional until GN0 has compatible urban scenes/tasks. |

Primary starting sources:

- VLN-CE official repository: https://github.com/jacobkrantz/VLN-CE
- StreamVLN project: https://streamvln.github.io/
- NavFoM project: https://pku-epic.github.io/NavFoM-Web/
- InternNav repository: https://github.com/InternRobotics/InternNav

## Eligible New Models To Add

These satisfy the post-2025 cutoff as of 2026-08-04. They are candidates, not
all guaranteed implementation targets.

| Priority | Model | First public date | Task fit | Why add | Availability / risk |
| --- | --- | --- | --- | --- | --- |
| P0 | Robostral Navigate | 2026-07-22 arXiv | VLN-CE, RGB-only instruction following, cross-embodiment | Claims SOTA on R2R-CE/RxR-CE with only monocular RGB; strong direct comparator for BAE-style visual navigation. | No public checkpoint found; treat as paper/result target until public weights or API access are available. Source: https://arxiv.org/abs/2607.20785 |
| P0 | ABot-N1 | 2026-07-11 arXiv | Point-goal, object-goal, POI-goal, instruction following, person following | Strong match for GN0 human-centric goals because it includes person-following and pixel-goal slow/fast control. | Benchmark/evaluator artifacts are public, but no model checkpoint was found; block native model eval until weights exist. Sources: https://arxiv.org/abs/2607.10383 and https://amap-cvlab.github.io/ABot-Navigation/ABot-N1/ |
| P0 | Qwen-RobotNav | 2026-06-16 arXiv | VLN-CE, ObjectNav, target tracking, EQA, autonomous driving | Broad multi-task navigation model with configurable observation protocol; good stress test for agentic mission control. | Official repo says no model-weight release planned, so use as paper-only benchmark or API/partner target. Sources: https://arxiv.org/abs/2606.18112 and https://github.com/QwenLM/Qwen-RobotNav |
| P1 | FutureNav | 2026-06-29 arXiv | VLN-CE instruction following | Adds explicit world-action modeling and future-state objectives; useful for testing whether future prediction helps dynamic humans. | Public Hugging Face checkpoint found; fetch into `model_zoo/futurenav` before adapter work. Sources: https://arxiv.org/abs/2606.30367 and https://linglingxiansen.github.io/FutureNav/ |
| P1 | AwareVLN | 2026-05-21 arXiv | Self-aware VLN, dynamic correction, VLN-CE-style instruction following | Useful for evaluating uncertainty/self-correction on GN0 missions where plans become invalid around humans. | Public project, code, dataset, and Hugging Face checkpoints found; fetch into `model_zoo/awarevln` before adapter work. Sources: https://gwxuan.github.io/AwareVLN/ and https://huggingface.co/gwx22/AwareVLN-ck |
| P1 | GA-VLN | 2026-05-21 arXiv | Geometry-aware VLN with RGB-D/BEV representation | Strong direct VLN-CE-style candidate for testing whether geometry-aware BEV inputs help in 3DGS scenes. | Public Hugging Face model found; needs RGB-D/BEV observation adapter audit before native GN0 eval. Sources: https://huggingface.co/jahhao/gavln_official and https://arxiv.org/abs/2605.22036 |
| P1 | TIC-VLA | 2026-02-02 arXiv | Dynamic, human-centric, language-guided robot navigation | Directly targets asynchronous reasoning/control under latency in dynamic environments; highly relevant to dynamic-human benchmark. | Public checkpoint found; likely requires its DynaNav simulator assumptions or an adapter. Source: https://arxiv.org/abs/2602.02459 |
| P1 | ReflectVLN | 2026-07-14 arXiv | Reflective VLN with history-aware correction | Relevant to failure recovery and dynamic mission replanning. | Code link found, but checkpoint status still needs source verification before native GN0 scheduling. Sources: https://huggingface.co/papers/2607.12680 and https://github.com/AIprogrammer/ReflectVLN |
| P1 | VLingNav | 2026-01-13 arXiv | Long-horizon embodied navigation, ObjectNav, ImageNav, tracking | Adaptive reasoning plus persistent visual-linguistic memory fits mission streams and repeated exploration. | No public checkpoint found; block native model eval until weights exist. Source: https://arxiv.org/abs/2601.08665 |
| P2 | Hydra-Nav | 2026-02-10 arXiv | Object-goal navigation | Strong ObjectNav/search candidate with adaptive slow/fast reasoning and a search-efficiency metric. | Good for object-search mission families; less direct for pure VLN. Source: https://arxiv.org/abs/2602.09972 |
| P2 | SanD-Planner | 2026-01-31 arXiv | Local planning in cluttered/dynamic navigation | Useful as a low-level planner comparator for safety and smoothness, not a full language agent. | Add only if GN0 exposes local-planner interfaces. Source: https://arxiv.org/abs/2602.00923 |
| P2 | VLN-Cache | 2026-04-29 arXiv | Training-free acceleration for MLLM-based VLN | Useful if newer MLLM/VLN adapters are too slow for long mission streams. | Not a standalone navigator; evaluate only as a runtime optimization layer. Source: https://www.alphaxiv.org/overview/2603.07080v3 |

## Checkpoint Readiness

Detailed checkpoint status is tracked in
`docs/navigation_model_eval_matrix.tsv`.

Machine-readable filtering is available through:

```bash
python3 vln_model_registry.py --bucket new_post_2025 --native-runnable --json
python3 plan_vln_evaluations.py --bucket new_post_2025 --native-runnable --json
python3 vln_adapter_registry.py --bucket new_post_2025 --summary
python3 prepare_vln_checkpoints.py --bucket new_post_2025 --native-runnable --missing-only --json
python3 export_vln_adapter_inputs.py --source /Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples --result-path /private/tmp/gn0_vln_adapter_inputs
python3 run_vln_native_eval.py --model human_eval_json_policies --mission-source /Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples --result-path /private/tmp/gn0_native_dispatcher_replay
python3 vln_eval_results.py --model human_eval_json_policies --from-replay-summary /private/tmp/gn0_navdp_all_mission_examples/summary.json --json
```

The registry enforces the `2026-01-01` cutoff for `new_post_2025` rows by
default; use `--no-validate` only for inspection of intentionally invalid draft
rows.

Current local status:

- No checkpoint files are present under `model_zoo` or `data/checkpoints` in
  this checkout.
- GN-BAE is the current GN0 reference model and has a public Hugging Face
  checkpoint, but it still needs to be fetched into `model_zoo/bae`.
- The five human-centric JSON policies do not need checkpoints and now run
  through the same dispatcher used for native model evaluation planning.
- FutureNav, AwareVLN, GA-VLN, and TIC-VLA have public checkpoint artifacts and
  are the post-2025 candidate models found to be fetchable right now. The
  planner now emits concrete `run_vln_native_eval.py` commands for them, but
  marks each as `adapter_required` until its adapter module and local checkpoint
  exist.
- `prepare_vln_checkpoints.py` emits exact Hugging Face download commands for
  GN-BAE, FutureNav, AwareVLN, GA-VLN, and TIC-VLA. It does not download by
  default; use `--execute` only on a machine with network access and enough disk.
- FutureNav, AwareVLN, GA-VLN, and TIC-VLA have importable adapter stubs under
  `vln_adapters/`. These stubs are deliberately marked `stub`, so readiness
  remains false even if a local checkpoint directory appears before the native
  observation/action bridge is implemented.
- Native Python adapters dispatched through `run_vln_native_eval.py` now produce
  the same `VLNEvaluationResult` row shape as replay and BAE log imports.
- `export_vln_adapter_inputs.py` produces compact per-mission
  `adapter_inputs.jsonl` records for native adapter implementation. On the full
  NavDP example directory it emits 115 rows across 55 episodes, all eight
  mission families, and currently reports zero missing instructions or goals.
- Robostral Navigate, Qwen-RobotNav, ABot-N1, ReflectVLN, VLingNav, Hydra-Nav, and
  SanD-Planner should not be scheduled as native model runs until public
  weights, API access, or partner artifacts are available.

Checkpoint gate for implementation:

1. Do not create a native GN0 runner for a model unless
   `checkpoint_status` is `PUBLIC_READY`, `NO_CHECKPOINT_NEEDED`, or an
   approved private/API source exists.
2. Paper-only models can appear in reports only as `external_reported`, never
   as reproduced GN0 runs.
3. Keep large dataset downloads separate from model checkpoint downloads.
   TIC-VLA is the important case: the model checkpoint is listed in a dataset
   repository whose full file size is much larger than the checkpoint needed for
   evaluation.

Checkpoint fetch targets:

| Model | Fetch target | Use before |
| --- | --- | --- |
| GN-BAE | `model_zoo/bae` from `https://huggingface.co/TeleEmbodied/GN-BAE` | Reproducing the current InteriorGS reference run. |
| FutureNav | `model_zoo/futurenav` from `https://huggingface.co/llxs/FutureNav/tree/main/FutureNav-4B-Base` | Building the first post-2025 native model adapter. |
| AwareVLN | `model_zoo/awarevln` from `https://huggingface.co/gwx22/AwareVLN-ck` | Testing self-correction/uncertainty behavior on dynamic mission scenarios. |
| GA-VLN | `model_zoo/ga_vln` from `https://huggingface.co/jahhao/gavln_official` | Testing geometry-aware BEV/RGB-D VLN inputs after observation adapter audit. |
| TIC-VLA | `model_zoo/tic_vla/TIC-VLA-model.ckpt` from `https://huggingface.co/datasets/handsomeYun/TIC-VLA` | Testing dynamic/human-centric VLA behavior after adapter feasibility review. |
| CMA / Seq2Seq VLN-CE | `data/checkpoints/CMA_PM_DA_Aug.pth` and `data/ddppo-models/gibson-2plus-resnet50.pth` | Restoring legacy VLN-CE baselines. |

Do not allocate native-run engineering time to Robostral Navigate, ABot-N1,
Qwen-RobotNav, ReflectVLN, VLingNav, Hydra-Nav, or SanD-Planner until their
checkpoint status changes in `docs/navigation_model_eval_matrix.tsv`.

## Proposed Evaluation Order

1. Freeze the taxonomy before building more evaluator code:
   `full VLN agent`, `object/search agent`, `person/social navigator`,
   `local planner`, and `paper-only external result`.
2. Use `vln_eval_results.py` as the result schema for native GN0 runs, replay
   runs, and external reproduced logs: model name, source date, run mode, sensor
   inputs, split, metrics, hardware, and runner status.
3. Run sanity baselines first: random, shortest-path/oracle, and the five
   existing human-centric JSON policies.
4. Reproduce the current BAE InteriorGS run and make it the reference row.
5. Add legacy comparators with available code/checkpoints: CMA first, then
   StreamVLN/NavFoM/InternNav-family only where assets are usable.
6. Add post-2025 candidates in checkpoint-gated native-run order:
   FutureNav first, then AwareVLN or GA-VLN depending on observation adapter
   feasibility, then TIC-VLA. Keep Robostral Navigate, ABot-N1,
   Qwen-RobotNav, ReflectVLN, VLingNav, Hydra-Nav, and SanD-Planner as blocked or
   `external_reported` until runnable weights/API access exist.

## Immediate TODOs

- [x] Create `docs/navigation_model_eval_matrix.tsv` or JSON with columns for
      model, status, source date, task fit, adapter owner, and evaluation state.
- [x] Add a machine-readable model-registry query for native-runnable and
      source-check-gated candidates.
- [x] Update the human-eval runner plan to include model adapters, not only
      deterministic JSON policies.
- [x] Decide whether closed/paper-only models are allowed as `external_reported`
      rows or must wait for runnable weights/API access.
- [x] Add a strict source-date check before marking any model as a "new"
      post-2025 addition.
- [x] Add a normalized result schema/importer for replay summaries and
      external-reported rows.
- [x] Add a native adapter contract plus dispatcher/readiness checks for BAE,
      replay baselines, and post-2025 candidate adapters.
- [x] Add GN0 native per-episode log import so BAE-style `log/*.json` outputs
      can be compared in the same result schema.
- [x] Add non-runnable adapter stubs and a checkpoint preparation planner for
      FutureNav, AwareVLN, GA-VLN, and TIC-VLA.
- [x] Make native Python adapter dispatch write normalized `vln_result.json`
      rows from `VLNAdapterRunResult` outputs.
- [x] Add a model-facing NavDP mission input exporter for native adapter authors.
- [ ] Pick the first runnable legacy comparator after BAE, likely CMA if the
      inherited VLN-CE dependencies can be restored.

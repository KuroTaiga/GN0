#!/usr/bin/env python3
"""Run publication baseline sweeps for NavDP human-centric splits."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parent
GN_BENCH_TOOLS = REPO_ROOT / "GN-Bench-Tools"
if str(GN_BENCH_TOOLS) not in sys.path:
    sys.path.insert(0, str(GN_BENCH_TOOLS))

from GN_Bench.human_eval.baseline_runner import (  # noqa: E402
    DEFAULT_POLICY_NAMES,
    POLICY_CLASSES,
    run_policy_assignment_sweep,
    summarize_policy_results,
)
from GN_Bench.human_eval.evaluator import HumanCentricEvaluator  # noqa: E402
from GN_Bench.human_eval.results import (  # noqa: E402
    replay_result_row,
    summarize_replay_result_rows,
    write_replay_result_rows,
)
from GN_Bench.human_eval.scenario_adapter import NavDPScenarioAdapter  # noqa: E402


JsonDict = dict[str, Any]
DEFAULT_NAVDP_ROOT = Path("/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner")
BASELINE_ROW_COLUMNS = (
    "baseline_name",
    "episode_id",
    "split",
    "dataset",
    "scene_id",
    "mission_type",
    "publication_variants",
    "mission_count",
    "assignment_count",
    "assigned_mission_count",
    "assignment_coverage",
    "oracle_assignment_match_rate",
    "success_rate",
    "mission_completion_rate",
    "navigation_error_m",
    "collision_rate",
    "total_collision_rate",
    "weighted_mission_score",
    "metrics_json",
)


def parse_args() -> argparse.Namespace:
    root_default = str(DEFAULT_NAVDP_ROOT) if DEFAULT_NAVDP_ROOT.exists() else None
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--splits",
        required=True,
        help="Publication split manifest JSON from Pathplanner.",
    )
    parser.add_argument(
        "--model-input-root",
        help="Directory containing model_inputs/<split>.jsonl. Counted and cross-referenced when present.",
    )
    parser.add_argument(
        "--hidden-gt-root",
        help="Directory containing hidden_gt/<split>.jsonl. Counted and cross-referenced when present.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        help="Output directory for baseline_results.jsonl/csv and summary.json.",
    )
    parser.add_argument(
        "--navdp-root",
        default=root_default,
        help="NavDP repo root used to resolve producer-relative scenario paths.",
    )
    parser.add_argument(
        "--policy",
        action="append",
        choices=sorted(POLICY_CLASSES),
        help="Policy name to run. Repeat to select multiple. Defaults to the five publication baselines.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Optional per-run episode cap.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the summary JSON after writing outputs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    adapter = NavDPScenarioAdapter(navdp_root=args.navdp_root)
    episodes_by_split = adapter.load_split_by_name(args.splits)
    episodes = [
        episode
        for split_name in sorted(episodes_by_split)
        for episode in sorted(
            episodes_by_split[split_name],
            key=lambda item: item.episode_id,
        )
    ]
    if args.limit > 0:
        episodes = episodes[: args.limit]
    if not episodes:
        raise RuntimeError(f"No episodes loaded from split manifest: {args.splits}")

    policy_names = list(args.policy or DEFAULT_POLICY_NAMES)
    evaluator = HumanCentricEvaluator()
    detailed_rows: list[JsonDict] = []
    baseline_rows: list[JsonDict] = []
    replay_rows: list[JsonDict] = []

    for episode in episodes:
        replay = evaluator.replay(episode)
        normalized_replay = replay_result_row(episode, replay)
        replay_rows.append(normalized_replay)
        policies: dict[str, JsonDict] = {}
        for policy_name in policy_names:
            policy_result = run_policy_assignment_sweep(policy_name, episode)
            policies[policy_name] = policy_result
            baseline_rows.append(
                _baseline_row(
                    policy_name=policy_name,
                    policy_result=policy_result,
                    replay_row=normalized_replay,
                )
            )
        detailed_rows.append(
            {
                "episode": {
                    "episode_id": episode.episode_id,
                    "split": episode.split or "unsplit",
                    "scenario_path": episode.scenario_path,
                    "dataset": episode.dataset,
                    "scene_id": episode.scene_id,
                    "mission_type": episode.mission_type,
                },
                "replay": replay_result_row(episode, replay),
                "policies": policies,
            }
        )

    replay_jsonl, replay_csv = write_replay_result_rows(replay_rows, output_root / "replay")
    baseline_jsonl = _write_jsonl(output_root / "baseline_results.jsonl", baseline_rows)
    baseline_csv = _write_baseline_csv(output_root / "baseline_results.csv", baseline_rows)
    (output_root / "episodes.json").write_text(
        json.dumps(detailed_rows, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    packet_summary = {
        "model_inputs": _jsonl_root_summary(args.model_input_root),
        "hidden_gt": _jsonl_root_summary(args.hidden_gt_root),
    }
    policy_summary = summarize_policy_results(detailed_rows)
    summary = {
        "schema_version": "human_publication_baselines_v0.1",
        "split_manifest": str(args.splits),
        "episode_count": len(episodes),
        "baseline_count": len(policy_names),
        "baseline_names": policy_names,
        "packet_summary": packet_summary,
        "result_paths": {
            "baseline_jsonl": str(baseline_jsonl),
            "baseline_csv": str(baseline_csv),
            "replay_jsonl": str(replay_jsonl),
            "replay_csv": str(replay_csv),
            "episodes_json": str(output_root / "episodes.json"),
        },
        "replay_summary": summarize_replay_result_rows(replay_rows),
        "policy_summary": policy_summary.get("policies", {}),
    }
    (output_root / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(json.dumps(summary["result_paths"], indent=2, sort_keys=True))


def _baseline_row(
    *,
    policy_name: str,
    policy_result: JsonDict,
    replay_row: JsonDict,
) -> JsonDict:
    metrics = policy_result.get("metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}
    return {
        "baseline_name": policy_name,
        "episode_id": replay_row.get("episode_id", ""),
        "split": replay_row.get("split", "unsplit"),
        "dataset": replay_row.get("dataset", ""),
        "scene_id": replay_row.get("scene_id", ""),
        "mission_type": replay_row.get("mission_type", ""),
        "publication_variants": replay_row.get("publication_variants", []),
        "mission_count": replay_row.get("mission_count", 0),
        "assignment_count": metrics.get("assignment_count", 0),
        "assigned_mission_count": metrics.get("assigned_mission_count", 0),
        "assignment_coverage": metrics.get("assignment_coverage"),
        "oracle_assignment_match_rate": metrics.get("oracle_assignment_match_rate"),
        "success_rate": replay_row.get("success_rate"),
        "mission_completion_rate": replay_row.get("mission_completion_rate"),
        "navigation_error_m": replay_row.get("navigation_error_m"),
        "collision_rate": replay_row.get("collision_rate"),
        "total_collision_rate": replay_row.get("total_collision_rate"),
        "weighted_mission_score": replay_row.get("weighted_mission_score"),
        "metrics_json": json.dumps(metrics, sort_keys=True, separators=(",", ":")),
    }


def _write_jsonl(path: Path, rows: Iterable[JsonDict]) -> Path:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in materialized:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return path


def _write_baseline_csv(path: Path, rows: Iterable[JsonDict]) -> Path:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(BASELINE_ROW_COLUMNS))
        writer.writeheader()
        for row in materialized:
            writer.writerow(
                {
                    column: _csv_value(row.get(column))
                    for column in BASELINE_ROW_COLUMNS
                }
            )
    return path


def _jsonl_root_summary(root: str | Path | None) -> JsonDict:
    if not root:
        return {"available": False, "record_count": 0, "by_split": {}}
    path = Path(root)
    if not path.is_dir():
        return {
            "available": False,
            "record_count": 0,
            "by_split": {},
            "path": str(path),
        }
    by_split: dict[str, int] = {}
    for jsonl_path in sorted(path.glob("*.jsonl")):
        by_split[jsonl_path.stem] = _jsonl_line_count(jsonl_path)
    return {
        "available": True,
        "path": str(path),
        "record_count": sum(by_split.values()),
        "by_split": by_split,
    }


def _jsonl_line_count(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def _csv_value(value: Any) -> Any:
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return value


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run replay and JSON-policy evaluation on NavDP mission artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent
GN_BENCH_TOOLS = REPO_ROOT / "GN-Bench-Tools"
if str(GN_BENCH_TOOLS) not in sys.path:
    sys.path.insert(0, str(GN_BENCH_TOOLS))

from GN_Bench.human_eval.baseline_runner import (  # noqa: E402
    DEFAULT_POLICY_NAMES,
    POLICY_CLASSES,
    run_policies_on_episode,
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
DEFAULT_SOURCE = DEFAULT_NAVDP_ROOT / "tmp/mission_examples/example_manifest.json"


def parse_args() -> argparse.Namespace:
    source_default = str(DEFAULT_SOURCE) if DEFAULT_SOURCE.exists() else None
    root_default = str(DEFAULT_NAVDP_ROOT) if DEFAULT_NAVDP_ROOT.exists() else None

    parser = argparse.ArgumentParser(
        description="Evaluate NavDP human-centric mission JSON artifacts."
    )
    parser.add_argument(
        "--source",
        default=source_default,
        required=source_default is None,
        help="Scenario JSON, split/example manifest JSON, or directory of scenario JSON files.",
    )
    parser.add_argument(
        "--navdp-root",
        default=root_default,
        help="NavDP repo root used to resolve producer-relative manifest paths.",
    )
    parser.add_argument(
        "--result-path",
        default="tmp/navdp_human_eval",
        help="Directory for JSON evaluation outputs.",
    )
    parser.add_argument(
        "--mission-type",
        action="append",
        default=[],
        help="Optional mission type filter. May be passed multiple times.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit loaded episodes.")
    parser.add_argument(
        "--policies",
        nargs="+",
        choices=sorted(POLICY_CLASSES),
        default=list(DEFAULT_POLICY_NAMES),
        help="Baseline policies to run.",
    )
    parser.add_argument(
        "--skip-policies",
        action="store_true",
        help="Only run artifact replay metrics.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    adapter = NavDPScenarioAdapter(navdp_root=args.navdp_root)
    episodes = adapter.load_path(args.source)
    episodes = _filter_episodes(episodes, args.mission_type)
    if args.limit > 0:
        episodes = episodes[: args.limit]
    if not episodes:
        raise RuntimeError(f"No NavDP scenario episodes loaded from {args.source}")

    result_dir = Path(args.result_path)
    result_dir.mkdir(parents=True, exist_ok=True)

    evaluator = HumanCentricEvaluator()
    rows: list[JsonDict] = []
    result_rows: list[JsonDict] = []
    for episode in episodes:
        replay = evaluator.replay(episode)
        normalized_row = replay_result_row(episode, replay)
        result_rows.append(normalized_row)
        policies = (
            {}
            if args.skip_policies
            else run_policies_on_episode(episode, policy_names=list(args.policies))
        )
        row = {
            "episode": _episode_summary(episode),
            "replay": asdict(replay),
            "result_row": normalized_row,
            "policies": policies,
        }
        rows.append(row)
        (result_dir / f"{_safe_filename(episode.episode_id)}.json").write_text(
            json.dumps(row, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    result_rows_jsonl, result_rows_csv = write_replay_result_rows(result_rows, result_dir)
    summary = _summary(rows)
    canonical_summary = summarize_replay_result_rows(result_rows)
    summary.update(
        {
            key: value
            for key, value in canonical_summary.items()
            if key
            not in {
                "episode_count",
                "success_count",
                "total_missions",
                "total_events",
            }
        }
    )
    summary["result_tables"] = {
        "jsonl": str(result_rows_jsonl),
        "csv": str(result_rows_csv),
    }
    summary.update(summarize_policy_results(rows) if not args.skip_policies else {})
    (result_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (result_dir / "episodes.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


def _filter_episodes(episodes: list[Any], mission_types: list[str]) -> list[Any]:
    if not mission_types:
        return episodes
    allowed = set(mission_types)
    return [
        episode
        for episode in episodes
        if episode.mission_type in allowed
        or any(
            mission.get("mission_type") in allowed
            for mission in episode.payload.get("missions", [])
            if isinstance(mission, dict)
        )
    ]


def _episode_summary(episode: Any) -> JsonDict:
    return {
        "episode_id": episode.episode_id,
        "scenario_path": episode.scenario_path,
        "scene_id": episode.scene_id,
        "raw_scene_id": episode.raw_scene_id,
        "dataset": episode.dataset,
        "mission_type": episode.mission_type,
        "schema_version": episode.schema_version,
        "split": episode.split or "unsplit",
    }


def _summary(rows: list[JsonDict]) -> JsonDict:
    replay_metrics = [row["replay"]["metrics"] for row in rows]
    successes = [row["replay"]["success"] for row in rows]
    return {
        "episode_count": len(rows),
        "success_count": sum(1 for value in successes if value is True),
        "mean_completion_rate": _mean(
            metric.get("completion_rate", 0.0) for metric in replay_metrics
        ),
        "mean_mission_success_rate": _mean(
            metric.get("mission_success_rate") for metric in replay_metrics
        ),
        "total_missions": sum(int(metric.get("mission_count", 0)) for metric in replay_metrics),
        "total_events": sum(int(metric.get("event_count", 0)) for metric in replay_metrics),
    }


def _mean(values: Any) -> float | None:
    values = [float(value) for value in values if value is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _safe_filename(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


if __name__ == "__main__":
    main()

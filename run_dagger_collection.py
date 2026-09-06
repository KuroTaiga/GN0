#!/usr/bin/env python3
"""Collect publication DAgger iteration-000 teacher records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
GN_BENCH_TOOLS = REPO_ROOT / "GN-Bench-Tools"
if str(GN_BENCH_TOOLS) not in sys.path:
    sys.path.insert(0, str(GN_BENCH_TOOLS))

from GN_Bench.human_eval.baseline_runner import POLICY_CLASSES  # noqa: E402
from GN_Bench.human_eval.dagger import export_iteration_zero  # noqa: E402
from GN_Bench.human_eval.scenario_adapter import NavDPScenarioAdapter  # noqa: E402


DEFAULT_NAVDP_ROOT = Path("/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner")


def parse_args() -> argparse.Namespace:
    root_default = str(DEFAULT_NAVDP_ROOT) if DEFAULT_NAVDP_ROOT.exists() else None
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", required=True, help="Publication split manifest JSON.")
    parser.add_argument(
        "--model-input-root",
        help="Directory containing model_inputs/<split>.jsonl.",
    )
    parser.add_argument(
        "--hidden-gt-root",
        help="Directory containing hidden_gt/<split>.jsonl.",
    )
    parser.add_argument(
        "--policy",
        default="oracle_route_follower",
        choices=sorted(POLICY_CLASSES),
        help="Teacher policy used for iteration-000 collection.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of iterations to export. Currently only 1 is supported.",
    )
    parser.add_argument(
        "--episodes-per-split",
        type=int,
        default=0,
        help="Optional cap per split. Use 0 for all episodes.",
    )
    parser.add_argument("--output-root", required=True)
    parser.add_argument(
        "--navdp-root",
        default=root_default,
        help="NavDP repo root used to resolve producer-relative scenario paths.",
    )
    parser.add_argument("--model-family", default="json_policy")
    parser.add_argument("--random-seed", type=int, default=0)
    parser.add_argument("--policy-version")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.iterations != 1:
        raise ValueError("Only --iterations 1 is supported before online DAgger training lands.")

    adapter = NavDPScenarioAdapter(navdp_root=args.navdp_root)
    episodes_by_split = adapter.load_split_by_name(args.split)
    if not any(episodes_by_split.values()):
        raise RuntimeError(f"No episodes loaded from split manifest: {args.split}")

    summary = export_iteration_zero(
        episodes_by_split,
        output_root=args.output_root,
        model_input_root=args.model_input_root,
        hidden_gt_root=args.hidden_gt_root,
        policy_name=args.policy,
        episodes_per_split=args.episodes_per_split,
        model_family=args.model_family,
        random_seed=args.random_seed,
        policy_version=args.policy_version,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

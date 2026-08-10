#!/usr/bin/env python3
"""Export NavDP mission scenarios as model-facing VLN adapter input records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from vln_adapters.navdp_inputs import (
    build_navdp_adapter_inputs,
    summarize_adapter_inputs,
    write_adapter_inputs,
)


DEFAULT_NAVDP_ROOT = Path("/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner")
DEFAULT_SOURCE = DEFAULT_NAVDP_ROOT / "tmp/mission_examples"


def parse_args() -> argparse.Namespace:
    source_default = str(DEFAULT_SOURCE) if DEFAULT_SOURCE.exists() else None
    root_default = str(DEFAULT_NAVDP_ROOT) if DEFAULT_NAVDP_ROOT.exists() else None
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default=source_default,
        required=source_default is None,
        help="Scenario JSON, split/example manifest JSON, or directory of NavDP scenario JSON files.",
    )
    parser.add_argument(
        "--navdp-root",
        default=root_default,
        help="NavDP repo root used to resolve producer-relative manifest paths.",
    )
    parser.add_argument(
        "--result-path",
        default="tmp/vln_adapter_inputs",
        help="Directory for adapter_inputs.jsonl and summary.json.",
    )
    parser.add_argument(
        "--mission-type",
        action="append",
        default=[],
        help="Optional mission type filter. May be passed multiple times.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit exported mission rows.")
    parser.add_argument("--include-raw", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print exported rows instead of writing files.")
    parser.add_argument("--summary", action="store_true", help="Only print aggregate counts.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = build_navdp_adapter_inputs(
        args.source,
        navdp_root=args.navdp_root,
        mission_types=args.mission_type,
        limit=args.limit,
        include_raw=args.include_raw,
    )
    if not records:
        raise RuntimeError(f"No model-facing NavDP mission inputs loaded from {args.source}")

    if args.summary:
        print(json.dumps(summarize_adapter_inputs(records), indent=2, sort_keys=True))
        return
    if args.json:
        print(json.dumps([row.to_dict() for row in records], indent=2, sort_keys=True))
        return

    jsonl_path, summary_path = write_adapter_inputs(records, args.result_path)
    summary = summarize_adapter_inputs(records)
    summary.update(
        {
            "adapter_inputs_path": str(jsonl_path),
            "summary_path": str(summary_path),
        }
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

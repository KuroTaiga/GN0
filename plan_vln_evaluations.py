#!/usr/bin/env python3
"""Build a checkpoint-gated VLN evaluation plan for GN0/NavDP missions."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from vln_model_registry import (
    DEFAULT_MATRIX_PATH,
    VLNModelRecord,
    filter_records,
    load_model_matrix,
)
from vln_adapter_registry import assess_adapter


DEFAULT_NAVDP_MISSION_SOURCE = (
    Path("/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner") / "tmp/mission_examples"
)


@dataclass(frozen=True)
class VLNEvaluationPlanRow:
    model: str
    bucket: str
    priority: str
    source_date: str
    checkpoint_status: str
    local_target: str
    local_status: str
    run_mode: str
    adapter_status: str
    ready_to_run: bool
    mission_source: str
    result_path: str
    command: str
    blocker: str


def build_evaluation_plan(
    records: Iterable[VLNModelRecord],
    *,
    mission_source: str | Path = DEFAULT_NAVDP_MISSION_SOURCE,
    result_root: str | Path = "tmp/vln_eval_plan",
    check_imports: bool = False,
) -> list[VLNEvaluationPlanRow]:
    mission_source = str(mission_source)
    result_root = Path(result_root)
    rows = [
        _plan_record(
            record,
            mission_source=mission_source,
            result_root=result_root,
            check_imports=check_imports,
        )
        for record in records
    ]
    return sorted(rows, key=lambda row: (row.priority, row.model))


def summarize_plan(rows: Iterable[VLNEvaluationPlanRow]) -> dict[str, object]:
    plan_rows = list(rows)
    return {
        "plan_count": len(plan_rows),
        "ready_to_run_count": sum(1 for row in plan_rows if row.ready_to_run),
        "adapter_required_count": sum(
            1 for row in plan_rows if row.adapter_status == "adapter_required"
        ),
        "blocked_count": sum(1 for row in plan_rows if row.run_mode == "blocked"),
        "source_check_required_count": sum(
            1 for row in plan_rows if row.adapter_status == "source_check_required"
        ),
        "external_reported_count": sum(
            1 for row in plan_rows if row.run_mode == "external_reported"
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX_PATH))
    parser.add_argument("--mission-source", default=str(DEFAULT_NAVDP_MISSION_SOURCE))
    parser.add_argument("--result-root", default="tmp/vln_eval_plan")
    parser.add_argument("--bucket")
    parser.add_argument("--priority")
    parser.add_argument("--native-runnable", action="store_true")
    parser.add_argument("--needs-source-check", action="store_true")
    parser.add_argument("--blocked", action="store_true")
    parser.add_argument("--ready-only", action="store_true")
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Check Python imports for adapter modules and declared dependencies.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of TSV.")
    parser.add_argument("--summary", action="store_true", help="Emit only aggregate counts.")
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Load the matrix without enforcing the post-2025 source-date cutoff.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = filter_records(
        load_model_matrix(args.matrix, validate=not args.no_validate),
        bucket=args.bucket,
        priority=args.priority,
        native_runnable=args.native_runnable,
        needs_source_check=args.needs_source_check,
        blocked=args.blocked,
    )
    rows = build_evaluation_plan(
        records,
        mission_source=args.mission_source,
        result_root=args.result_root,
        check_imports=args.check_imports,
    )
    if args.ready_only:
        rows = [row for row in rows if row.ready_to_run]
    if args.summary:
        print(json.dumps(summarize_plan(rows), indent=2, sort_keys=True))
        return
    if args.json:
        print(json.dumps([asdict(row) for row in rows], indent=2, sort_keys=True))
        return
    _print_tsv(rows)


def _plan_record(
    record: VLNModelRecord,
    *,
    mission_source: str,
    result_root: Path,
    check_imports: bool = False,
) -> VLNEvaluationPlanRow:
    result_path = str(result_root / _safe_name(record.model))
    readiness = assess_adapter(
        record,
        mission_source=mission_source,
        result_path=result_path,
        check_imports=check_imports,
    )

    return VLNEvaluationPlanRow(
        model=record.model,
        bucket=record.bucket,
        priority=record.priority,
        source_date=record.source_date,
        checkpoint_status=record.checkpoint_status,
        local_target=record.local_target,
        local_status=record.local_status,
        run_mode=readiness.run_mode,
        adapter_status=readiness.adapter_status,
        ready_to_run=readiness.ready_to_run,
        mission_source=mission_source,
        result_path=result_path,
        command=readiness.command,
        blocker=readiness.blocker,
    )


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


def _print_tsv(rows: list[VLNEvaluationPlanRow]) -> None:
    fieldnames = list(VLNEvaluationPlanRow.__dataclass_fields__)
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, delimiter="\t")
    writer.writeheader()
    for row in rows:
        writer.writerow(asdict(row))


if __name__ == "__main__":
    main()

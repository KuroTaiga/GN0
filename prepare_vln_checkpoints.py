#!/usr/bin/env python3
"""Build or execute checkpoint-fetch commands for GN0 VLN model evaluation."""

from __future__ import annotations

import argparse
import csv
import json
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from vln_model_registry import (
    DEFAULT_MATRIX_PATH,
    REPO_ROOT,
    VLNModelRecord,
    filter_records,
    load_model_matrix,
)


@dataclass(frozen=True)
class CheckpointFetchSpec:
    model: str
    source: str
    command_template: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class CheckpointPlanRow:
    model: str
    bucket: str
    checkpoint_status: str
    local_target: str
    local_path: str
    checkpoint_ready: bool
    fetch_supported: bool
    command: str
    blocker: str
    notes: str


FETCH_SPECS: dict[str, CheckpointFetchSpec] = {
    "GN-BAE": CheckpointFetchSpec(
        model="GN-BAE",
        source="https://huggingface.co/TeleEmbodied/GN-BAE",
        command_template=(
            "huggingface-cli",
            "download",
            "TeleEmbodied/GN-BAE",
            "--local-dir",
            "{local_path}",
        ),
        notes="Current GN0 reference checkpoint.",
    ),
    "FutureNav": CheckpointFetchSpec(
        model="FutureNav",
        source="https://huggingface.co/llxs/FutureNav/tree/main/FutureNav-4B-Base",
        command_template=(
            "huggingface-cli",
            "download",
            "llxs/FutureNav",
            "--include",
            "FutureNav-4B-Base/*",
            "--local-dir",
            "{local_path}",
        ),
        notes="Download only the FutureNav-4B-Base subtree.",
    ),
    "AwareVLN": CheckpointFetchSpec(
        model="AwareVLN",
        source="https://huggingface.co/gwx22/AwareVLN-ck",
        command_template=(
            "huggingface-cli",
            "download",
            "gwx22/AwareVLN-ck",
            "--local-dir",
            "{local_path}",
        ),
        notes="Checkpoint card lists NavILA and AwareVLN artifacts.",
    ),
    "GA_VLN": CheckpointFetchSpec(
        model="GA_VLN",
        source="https://huggingface.co/jahhao/gavln_official",
        command_template=(
            "huggingface-cli",
            "download",
            "jahhao/gavln_official",
            "--local-dir",
            "{local_path}",
        ),
        notes="GA-VLN official Hugging Face model.",
    ),
    "TIC_VLA": CheckpointFetchSpec(
        model="TIC_VLA",
        source="https://huggingface.co/datasets/handsomeYun/TIC-VLA",
        command_template=(
            "huggingface-cli",
            "download",
            "handsomeYun/TIC-VLA",
            "--repo-type",
            "dataset",
            "--include",
            "TIC-VLA-model.ckpt",
            "--local-dir",
            "{local_path}",
        ),
        notes="Avoid the full dataset; fetch only the model checkpoint.",
    ),
}


def build_checkpoint_plan(records: Iterable[VLNModelRecord]) -> list[CheckpointPlanRow]:
    rows = [_plan_record(record) for record in records]
    return sorted(rows, key=lambda row: (row.bucket, row.model))


def summarize_checkpoint_plan(rows: Iterable[CheckpointPlanRow]) -> dict[str, object]:
    plan = list(rows)
    return {
        "plan_count": len(plan),
        "checkpoint_ready_count": sum(1 for row in plan if row.checkpoint_ready),
        "fetch_supported_count": sum(1 for row in plan if row.fetch_supported),
        "missing_fetchable_count": sum(
            1 for row in plan if row.fetch_supported and not row.checkpoint_ready
        ),
        "blocked_count": sum(1 for row in plan if row.blocker),
        "models": [row.model for row in plan],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX_PATH))
    parser.add_argument("--model", action="append", default=[])
    parser.add_argument("--bucket")
    parser.add_argument("--priority")
    parser.add_argument("--native-runnable", action="store_true")
    parser.add_argument("--missing-only", action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of TSV.")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run supported fetch commands for missing checkpoints.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = filter_records(
        load_model_matrix(args.matrix),
        bucket=args.bucket,
        priority=args.priority,
        native_runnable=args.native_runnable,
    )
    if args.model:
        allowed = set(args.model)
        records = [record for record in records if record.model in allowed]
    rows = build_checkpoint_plan(records)
    if args.missing_only:
        rows = [row for row in rows if not row.checkpoint_ready]
    if args.execute:
        _execute_plan(rows)
        rows = build_checkpoint_plan(records)
        if args.missing_only:
            rows = [row for row in rows if not row.checkpoint_ready]

    if args.summary:
        print(json.dumps(summarize_checkpoint_plan(rows), indent=2, sort_keys=True))
    elif args.json:
        print(json.dumps([asdict(row) for row in rows], indent=2, sort_keys=True))
    else:
        _print_tsv(rows)


def _plan_record(record: VLNModelRecord) -> CheckpointPlanRow:
    local_path = _local_path(record.local_target)
    checkpoint_ready = _checkpoint_ready(record, local_path)
    spec = FETCH_SPECS.get(record.model)
    fetch_supported = spec is not None and record.can_schedule_native_eval
    command = _format_command(spec, local_path) if spec and fetch_supported else ""
    blocker = ""
    if record.checkpoint_status == "NO_CHECKPOINT_NEEDED":
        fetch_supported = False
    elif record.is_blocked:
        blocker = "checkpoint source is blocked by registry policy"
    elif record.needs_source_check:
        blocker = "verify checkpoint source before fetching"
    elif not fetch_supported and not checkpoint_ready:
        blocker = "no checkpoint fetch recipe exists"

    return CheckpointPlanRow(
        model=record.model,
        bucket=record.bucket,
        checkpoint_status=record.checkpoint_status,
        local_target=record.local_target,
        local_path=str(local_path) if local_path is not None else "",
        checkpoint_ready=checkpoint_ready,
        fetch_supported=fetch_supported,
        command=command,
        blocker=blocker,
        notes=spec.notes if spec else record.notes,
    )


def _execute_plan(rows: list[CheckpointPlanRow]) -> None:
    for row in rows:
        if row.checkpoint_ready or not row.fetch_supported:
            continue
        if not row.command:
            continue
        if row.local_path:
            Path(row.local_path).mkdir(parents=True, exist_ok=True)
        subprocess.run(shlex.split(row.command), check=True)


def _local_path(local_target: str) -> Path | None:
    if not local_target or local_target == "n/a":
        return None
    path = Path(local_target)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def _checkpoint_ready(record: VLNModelRecord, local_path: Path | None) -> bool:
    if record.checkpoint_status == "NO_CHECKPOINT_NEEDED":
        return True
    return local_path is not None and local_path.exists()


def _format_command(spec: CheckpointFetchSpec, local_path: Path | None) -> str:
    values = {"local_path": str(local_path or "")}
    return " ".join(shlex.quote(part.format(**values)) for part in spec.command_template)


def _print_tsv(rows: list[CheckpointPlanRow]) -> None:
    fieldnames = list(CheckpointPlanRow.__dataclass_fields__)
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, delimiter="\t")
    writer.writeheader()
    for row in rows:
        writer.writerow(asdict(row))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Read and query the GN0 navigation model evaluation matrix."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_MATRIX_PATH = REPO_ROOT / "docs/navigation_model_eval_matrix.tsv"
NEW_MODEL_CUTOFF = date(2026, 1, 1)

NATIVE_READY_STATUSES = {
    "PUBLIC_READY",
    "NO_CHECKPOINT_NEEDED",
}
ACCELERATOR_STATUSES = {"NO_CHECKPOINT_NEEDED_ACCELERATOR"}
NEEDS_SOURCE_CHECK_STATUSES = {
    "CHECKPOINT_REQUIRED",
    "CODE_PUBLIC_CHECKPOINT_UNKNOWN",
    "PUBLIC_MODEL_LINK_UNVERIFIED",
}
BLOCKED_STATUSES = {
    "NO_PUBLIC_CHECKPOINT_FOUND",
    "BENCHMARK_READY_MODEL_NOT_RELEASED",
    "NO_PUBLIC_CHECKPOINT_BY_POLICY",
    "PROMISED_NOT_READY",
}


@dataclass(frozen=True)
class VLNModelRecord:
    model: str
    bucket: str
    source_date: str
    priority: str
    checkpoint_status: str
    official_checkpoint_source: str
    local_target: str
    local_status: str
    notes: str

    @property
    def is_new_candidate(self) -> bool:
        return self.bucket == "new_post_2025"

    @property
    def can_schedule_native_eval(self) -> bool:
        return self.checkpoint_status in NATIVE_READY_STATUSES

    @property
    def needs_source_check(self) -> bool:
        return self.checkpoint_status in NEEDS_SOURCE_CHECK_STATUSES

    @property
    def is_accelerator(self) -> bool:
        return self.checkpoint_status in ACCELERATOR_STATUSES

    @property
    def is_blocked(self) -> bool:
        return self.checkpoint_status in BLOCKED_STATUSES

    @property
    def parsed_source_date(self) -> date | None:
        try:
            return date.fromisoformat(self.source_date)
        except ValueError:
            return None

    @property
    def source_date_passes_new_cutoff(self) -> bool:
        if not self.is_new_candidate:
            return True
        parsed = self.parsed_source_date
        return parsed is not None and parsed >= NEW_MODEL_CUTOFF


def load_model_matrix(
    path: str | Path = DEFAULT_MATRIX_PATH,
    *,
    validate: bool = True,
) -> list[VLNModelRecord]:
    matrix_path = Path(path)
    with matrix_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        records = [VLNModelRecord(**row) for row in reader]
    if validate:
        errors = validate_model_matrix(records)
        if errors:
            raise ValueError("Invalid VLN model matrix:\n- " + "\n- ".join(errors))
    return records


def validate_model_matrix(records: Iterable[VLNModelRecord]) -> list[str]:
    errors: list[str] = []
    for record in records:
        if not record.is_new_candidate:
            continue
        if record.parsed_source_date is None:
            errors.append(
                f"{record.model}: new_post_2025 rows need YYYY-MM-DD source_date"
            )
        elif record.parsed_source_date < NEW_MODEL_CUTOFF:
            errors.append(
                f"{record.model}: source_date {record.source_date} predates "
                f"{NEW_MODEL_CUTOFF.isoformat()} cutoff"
            )
    return errors


def filter_records(
    records: Iterable[VLNModelRecord],
    *,
    bucket: str | None = None,
    priority: str | None = None,
    native_runnable: bool = False,
    needs_source_check: bool = False,
    blocked: bool = False,
) -> list[VLNModelRecord]:
    filtered = list(records)
    if bucket:
        filtered = [record for record in filtered if record.bucket == bucket]
    if priority:
        filtered = [record for record in filtered if record.priority == priority]
    if native_runnable:
        filtered = [record for record in filtered if record.can_schedule_native_eval]
    if needs_source_check:
        filtered = [record for record in filtered if record.needs_source_check]
    if blocked:
        filtered = [record for record in filtered if record.is_blocked]
    return sorted(filtered, key=lambda record: (record.priority, record.model))


def summarize_records(records: Iterable[VLNModelRecord]) -> dict[str, object]:
    rows = list(records)
    return {
        "model_count": len(rows),
        "new_candidate_count": sum(1 for row in rows if row.is_new_candidate),
        "native_runnable_count": sum(1 for row in rows if row.can_schedule_native_eval),
        "accelerator_count": sum(1 for row in rows if row.is_accelerator),
        "source_check_count": sum(1 for row in rows if row.needs_source_check),
        "blocked_count": sum(1 for row in rows if row.is_blocked),
        "new_candidate_source_date_invalid_count": sum(
            1 for row in rows if row.is_new_candidate and not row.source_date_passes_new_cutoff
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX_PATH))
    parser.add_argument("--bucket")
    parser.add_argument("--priority")
    parser.add_argument("--native-runnable", action="store_true")
    parser.add_argument("--needs-source-check", action="store_true")
    parser.add_argument("--blocked", action="store_true")
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
    if args.summary:
        print(json.dumps(summarize_records(records), indent=2, sort_keys=True))
        return
    if args.json:
        print(json.dumps([asdict(record) for record in records], indent=2, sort_keys=True))
        return
    _print_tsv(records)


def _print_tsv(records: list[VLNModelRecord]) -> None:
    fieldnames = list(VLNModelRecord.__dataclass_fields__)
    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=fieldnames,
        delimiter="\t",
    )
    writer.writeheader()
    for record in records:
        writer.writerow(asdict(record))


if __name__ == "__main__":
    main()

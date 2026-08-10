#!/usr/bin/env python3
"""Dispatch model-specific VLN evaluation runs through the GN0 adapter registry."""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from vln_adapter_registry import assess_adapter, adapter_spec_for
from vln_eval_results import (
    result_from_gn0_log_dir,
    result_from_native_adapter_run,
    result_from_replay_summary,
)
from vln_model_registry import DEFAULT_MATRIX_PATH, VLNModelRecord, load_model_matrix


JsonDict = dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX_PATH))
    parser.add_argument("--model", required=True)
    parser.add_argument("--mission-source", required=True)
    parser.add_argument("--result-path", required=True)
    parser.add_argument("--split", default="mission_examples")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report adapter readiness and the command that would run.",
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Check adapter imports during dry-run diagnostics.",
    )
    parser.add_argument(
        "--allow-not-ready",
        action="store_true",
        help="Return exit code 0 for not-ready dry-run diagnostics.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = _record_by_model(load_model_matrix(args.matrix), args.model)
    result_path = Path(args.result_path)
    readiness = assess_adapter(
        record,
        mission_source=args.mission_source,
        result_path=result_path,
        check_imports=args.check_imports or not args.dry_run,
    )

    if args.dry_run:
        print(json.dumps(asdict(readiness), indent=2, sort_keys=True))
        if readiness.ready_to_run or args.allow_not_ready:
            return
        raise SystemExit(2)

    if not readiness.ready_to_run:
        print(json.dumps(asdict(readiness), indent=2, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)

    result_path.mkdir(parents=True, exist_ok=True)
    if readiness.run_mode == "json_policy_replay":
        _run_replay(record, args.mission_source, result_path, args.split)
    elif readiness.run_mode == "native_gn0_bae":
        _run_bae(record, result_path, args.split)
    elif readiness.run_mode == "native_adapter":
        _run_python_adapter(record, args.mission_source, result_path, args.split)
    else:
        raise RuntimeError(f"Unsupported runnable mode: {readiness.run_mode}")


def _run_replay(
    record: VLNModelRecord,
    mission_source: str,
    result_path: Path,
    split: str,
) -> None:
    subprocess.run(
        [
            sys.executable,
            "eval_navdp_missions.py",
            "--source",
            mission_source,
            "--result-path",
            str(result_path),
        ],
        check=True,
    )
    result = result_from_replay_summary(
        result_path / "summary.json",
        record,
        mission_source=mission_source,
        split=split,
    )
    _write_result(result_path, asdict(result))


def _run_bae(record: VLNModelRecord, result_path: Path, split: str) -> None:
    subprocess.run(
        [
            "./eval_bae_InteriorGS.sh",
            "--model-path",
            record.local_target,
            "--save-path",
            str(result_path),
        ],
        check=True,
    )
    log_dir = result_path / "log"
    if log_dir.exists():
        result = result_from_gn0_log_dir(
            log_dir,
            record,
            split=split,
            result_path=result_path,
            run_mode="native_gn0_bae",
        )
        _write_result(result_path, asdict(result))


def _run_python_adapter(
    record: VLNModelRecord,
    mission_source: str,
    result_path: Path,
    split: str,
) -> None:
    from vln_adapters.base import VLNAdapterContext

    spec = adapter_spec_for(record)
    module = importlib.import_module(spec.adapter_module)
    adapter_cls = getattr(module, spec.adapter_class)
    adapter = adapter_cls(
        VLNAdapterContext(
            model=record.model,
            model_path=Path(record.local_target),
            mission_source=Path(mission_source),
            result_path=result_path,
            split=split,
        )
    )
    run_result = adapter.run()
    result = result_from_native_adapter_run(
        run_result,
        record,
        mission_source=mission_source,
        split=split,
        result_path=result_path,
    )
    _write_result(result_path, asdict(result))


def _record_by_model(records: list[VLNModelRecord], model: str) -> VLNModelRecord:
    for record in records:
        if record.model == model:
            return record
    raise ValueError(f"Unknown model in matrix: {model}")


def _write_result(result_path: Path, payload: JsonDict) -> None:
    (result_path / "vln_result.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

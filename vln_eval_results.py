#!/usr/bin/env python3
"""Normalize VLN/native/replay evaluation outputs into comparable result rows."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from vln_model_registry import DEFAULT_MATRIX_PATH, VLNModelRecord, load_model_matrix


JsonDict = dict[str, Any]
DEFAULT_MISSION_SOURCE = "/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner/tmp/mission_examples"


@dataclass(frozen=True)
class VLNEvaluationResult:
    model: str
    bucket: str
    source_date: str
    run_mode: str
    runner_status: str
    mission_source: str
    split: str
    result_path: str
    sensor_inputs: str
    hardware: str
    episode_count: int
    total_missions: int
    total_events: int
    success_count: int
    mean_mission_success_rate: float | None
    mean_completion_rate: float | None
    metrics_json: str
    notes: str


def result_from_replay_summary(
    summary_path: str | Path,
    record: VLNModelRecord,
    *,
    mission_source: str = DEFAULT_MISSION_SOURCE,
    split: str = "mission_examples",
    run_mode: str = "json_policy_replay",
    runner_status: str = "completed",
    sensor_inputs: str = "navdp_artifact_replay",
    hardware: str = "local_python",
    notes: str = "",
) -> VLNEvaluationResult:
    summary_path = Path(summary_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if not isinstance(summary, dict):
        raise ValueError(f"Replay summary must be a JSON object: {summary_path}")
    return VLNEvaluationResult(
        model=record.model,
        bucket=record.bucket,
        source_date=record.source_date,
        run_mode=run_mode,
        runner_status=runner_status,
        mission_source=mission_source,
        split=split,
        result_path=str(summary_path.parent),
        sensor_inputs=sensor_inputs,
        hardware=hardware,
        episode_count=int(_number(summary.get("episode_count"), 0)),
        total_missions=int(_number(summary.get("total_missions"), 0)),
        total_events=int(_number(summary.get("total_events"), 0)),
        success_count=int(_number(summary.get("success_count"), 0)),
        mean_mission_success_rate=_optional_number(summary.get("mean_mission_success_rate")),
        mean_completion_rate=_optional_number(summary.get("mean_completion_rate")),
        metrics_json=json.dumps(summary, sort_keys=True, separators=(",", ":")),
        notes=notes,
    )


def result_from_external_payload(
    payload: JsonDict,
    record: VLNModelRecord,
) -> VLNEvaluationResult:
    """Create an external-reported row from a JSON payload.

    Expected payload keys mirror ``VLNEvaluationResult``; model identity comes
    from the registry record so paper-only rows cannot drift from the matrix.
    """

    return VLNEvaluationResult(
        model=record.model,
        bucket=record.bucket,
        source_date=record.source_date,
        run_mode=str(payload.get("run_mode", "external_reported")),
        runner_status=str(payload.get("runner_status", "external_reported")),
        mission_source=str(payload.get("mission_source", "")),
        split=str(payload.get("split", "")),
        result_path=str(payload.get("result_path", "")),
        sensor_inputs=str(payload.get("sensor_inputs", "")),
        hardware=str(payload.get("hardware", "")),
        episode_count=int(_number(payload.get("episode_count"), 0)),
        total_missions=int(_number(payload.get("total_missions"), 0)),
        total_events=int(_number(payload.get("total_events"), 0)),
        success_count=int(_number(payload.get("success_count"), 0)),
        mean_mission_success_rate=_optional_number(payload.get("mean_mission_success_rate")),
        mean_completion_rate=_optional_number(payload.get("mean_completion_rate")),
        metrics_json=_metrics_json(payload.get("metrics", payload)),
        notes=str(payload.get("notes", "")),
    )


def result_from_gn0_log_dir(
    log_dir: str | Path,
    record: VLNModelRecord,
    *,
    mission_source: str = "GN_Bench_native_dataset",
    split: str = "unknown",
    result_path: str | Path | None = None,
    run_mode: str = "native_gn0",
    runner_status: str = "completed",
    sensor_inputs: str = "gn0_env_observations",
    hardware: str = "local_native",
    notes: str = "",
) -> VLNEvaluationResult:
    log_dir = Path(log_dir)
    rows = _load_metric_rows(log_dir)
    episode_count = len(rows)
    success_values = [_optional_number(row.get("success")) for row in rows]
    oracle_success_values = [_optional_number(row.get("oracle_success")) for row in rows]
    metrics = {
        "episode_count": episode_count,
        "success_count": sum(1 for value in success_values if value and value > 0),
        "mean_success": _mean_optional(success_values),
        "mean_oracle_success": _mean_optional(oracle_success_values),
        "mean_spl": _mean_optional(_optional_number(row.get("spl")) for row in rows),
        "mean_path_length": _mean_optional(
            _optional_number(row.get("path_length")) for row in rows
        ),
        "mean_distance_to_goal": _mean_optional(
            _optional_number(row.get("distance_to_goal")) for row in rows
        ),
    }
    return VLNEvaluationResult(
        model=record.model,
        bucket=record.bucket,
        source_date=record.source_date,
        run_mode=run_mode,
        runner_status=runner_status,
        mission_source=mission_source,
        split=split,
        result_path=str(result_path or log_dir.parent),
        sensor_inputs=sensor_inputs,
        hardware=hardware,
        episode_count=episode_count,
        total_missions=episode_count,
        total_events=0,
        success_count=int(metrics["success_count"]),
        mean_mission_success_rate=metrics["mean_success"],
        mean_completion_rate=metrics["mean_oracle_success"],
        metrics_json=json.dumps(metrics, sort_keys=True, separators=(",", ":")),
        notes=notes,
    )


def result_from_native_adapter_run(
    run_result: Any,
    record: VLNModelRecord,
    *,
    mission_source: str = DEFAULT_MISSION_SOURCE,
    split: str = "mission_examples",
    result_path: str | Path | None = None,
    run_mode: str = "native_adapter",
    runner_status: str = "completed",
    sensor_inputs: str = "native_adapter_observations",
    hardware: str = "local_native",
    notes: str = "",
) -> VLNEvaluationResult:
    metrics = _native_adapter_metrics(run_result)
    episode_count = int(_number(metrics.get("episode_count"), 0))
    total_missions = int(
        _number(metrics.get("total_missions"), float(episode_count))
    )
    total_events = int(_number(metrics.get("total_events"), 0))
    success_count = int(_number(metrics.get("success_count"), 0))
    mean_success = _optional_number(
        metrics.get("mean_mission_success_rate", metrics.get("mean_success"))
    )
    if mean_success is None and episode_count > 0:
        mean_success = success_count / episode_count
    mean_completion = _optional_number(
        metrics.get("mean_completion_rate", metrics.get("mean_oracle_success"))
    )
    resolved_result_path = result_path or getattr(run_result, "result_path", "")

    return VLNEvaluationResult(
        model=record.model,
        bucket=record.bucket,
        source_date=record.source_date,
        run_mode=run_mode,
        runner_status=runner_status,
        mission_source=mission_source,
        split=split,
        result_path=str(resolved_result_path),
        sensor_inputs=sensor_inputs,
        hardware=hardware,
        episode_count=episode_count,
        total_missions=total_missions,
        total_events=total_events,
        success_count=success_count,
        mean_mission_success_rate=mean_success,
        mean_completion_rate=mean_completion,
        metrics_json=json.dumps(metrics, sort_keys=True, separators=(",", ":")),
        notes=notes,
    )


def summarize_results(results: Iterable[VLNEvaluationResult]) -> JsonDict:
    rows = list(results)
    completed = [row for row in rows if row.runner_status == "completed"]
    native = [row for row in rows if row.run_mode.startswith("native")]
    external = [row for row in rows if row.run_mode == "external_reported"]
    return {
        "result_count": len(rows),
        "completed_count": len(completed),
        "native_result_count": len(native),
        "external_reported_count": len(external),
        "best_mean_mission_success_rate": _max_optional(
            row.mean_mission_success_rate for row in rows
        ),
        "models": sorted({row.model for row in rows}),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX_PATH))
    parser.add_argument("--model", required=True)
    parser.add_argument("--from-replay-summary")
    parser.add_argument("--from-gn0-log-dir")
    parser.add_argument("--from-native-adapter-summary")
    parser.add_argument("--external-json")
    parser.add_argument("--mission-source", default=DEFAULT_MISSION_SOURCE)
    parser.add_argument("--split", default="mission_examples")
    parser.add_argument("--run-mode")
    parser.add_argument("--runner-status", default="completed")
    parser.add_argument("--sensor-inputs", default="navdp_artifact_replay")
    parser.add_argument("--hardware", default="local_python")
    parser.add_argument("--notes", default="")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of TSV.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = _record_by_model(load_model_matrix(args.matrix), args.model)
    if args.from_replay_summary:
        result = result_from_replay_summary(
            args.from_replay_summary,
            record,
            mission_source=args.mission_source,
            split=args.split,
            run_mode=args.run_mode or "json_policy_replay",
            runner_status=args.runner_status,
            sensor_inputs=args.sensor_inputs,
            hardware=args.hardware,
            notes=args.notes,
        )
    elif args.from_gn0_log_dir:
        result = result_from_gn0_log_dir(
            args.from_gn0_log_dir,
            record,
            mission_source=args.mission_source,
            split=args.split,
            run_mode=args.run_mode or "native_gn0",
            runner_status=args.runner_status,
            sensor_inputs=(
                args.sensor_inputs
                if args.sensor_inputs != "navdp_artifact_replay"
                else "gn0_env_observations"
            ),
            hardware=args.hardware if args.hardware != "local_python" else "local_native",
            notes=args.notes,
        )
    elif args.from_native_adapter_summary:
        payload = json.loads(
            Path(args.from_native_adapter_summary).read_text(encoding="utf-8")
        )
        if not isinstance(payload, dict):
            raise ValueError("--from-native-adapter-summary must point to a JSON object")
        result = result_from_native_adapter_run(
            _PayloadRunResult(payload, args.from_native_adapter_summary),
            record,
            mission_source=args.mission_source,
            split=args.split,
            run_mode=args.run_mode or "native_adapter",
            runner_status=args.runner_status,
            sensor_inputs=(
                args.sensor_inputs
                if args.sensor_inputs != "navdp_artifact_replay"
                else "native_adapter_observations"
            ),
            hardware=args.hardware if args.hardware != "local_python" else "local_native",
            notes=args.notes,
        )
    elif args.external_json:
        payload = json.loads(Path(args.external_json).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("--external-json must point to a JSON object")
        result = result_from_external_payload(payload, record)
    else:
        raise ValueError(
            "Provide --from-replay-summary, --from-gn0-log-dir, "
            "--from-native-adapter-summary, or --external-json"
        )

    if args.summary:
        print(json.dumps(summarize_results([result]), indent=2, sort_keys=True))
    elif args.json:
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
    else:
        _print_tsv([result])


def _record_by_model(records: Iterable[VLNModelRecord], model: str) -> VLNModelRecord:
    for record in records:
        if record.model == model:
            return record
    raise ValueError(f"Unknown model in matrix: {model}")


def _metrics_json(value: Any) -> str:
    if not isinstance(value, dict):
        value = {}
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _load_metric_rows(log_dir: Path) -> list[JsonDict]:
    if not log_dir.is_dir():
        raise FileNotFoundError(f"GN0 log directory does not exist: {log_dir}")
    rows: list[JsonDict] = []
    for path in sorted(log_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"GN0 metric log must be a JSON object: {path}")
        rows.append(payload)
    if not rows:
        raise ValueError(f"No GN0 metric JSON files found in: {log_dir}")
    return rows


@dataclass(frozen=True)
class _PayloadRunResult:
    metrics: JsonDict
    result_path: str
    summary_path: str | None = None


def _native_adapter_metrics(run_result: Any) -> JsonDict:
    metrics = getattr(run_result, "metrics", None)
    if isinstance(metrics, dict) and metrics:
        return dict(metrics)
    summary_path = getattr(run_result, "summary_path", None)
    if summary_path:
        path = Path(summary_path)
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError(f"Native adapter summary must be a JSON object: {path}")
            return payload
    return {}


def _number(value: Any, default: float) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    return default


def _optional_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _mean_optional(values: Iterable[float | None]) -> float | None:
    numbers = [value for value in values if value is not None]
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


def _max_optional(values: Iterable[float | None]) -> float | None:
    numbers = [value for value in values if value is not None]
    return max(numbers) if numbers else None


def _print_tsv(rows: list[VLNEvaluationResult]) -> None:
    fieldnames = list(VLNEvaluationResult.__dataclass_fields__)
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, delimiter="\t")
    writer.writeheader()
    for row in rows:
        writer.writerow(asdict(row))


if __name__ == "__main__":
    main()

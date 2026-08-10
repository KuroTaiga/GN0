#!/usr/bin/env python3
"""Assess native VLN adapter readiness and build GN0/NavDP runner commands."""

from __future__ import annotations

import argparse
import importlib
import json
import shlex
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from vln_model_registry import (
    DEFAULT_MATRIX_PATH,
    REPO_ROOT,
    VLNModelRecord,
    load_model_matrix,
)
from vln_adapters.base import (
    ADAPTER_STATUS_MISSING,
    ADAPTER_STATUS_NATIVE_READY,
    ADAPTER_STATUS_STUB,
)


@dataclass(frozen=True)
class VLNAdapterSpec:
    model: str
    runner: str
    adapter_module: str
    adapter_class: str
    implementation_status: str = ADAPTER_STATUS_NATIVE_READY
    required_python_modules: tuple[str, ...] = ()
    required_files: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class VLNAdapterReadiness:
    model: str
    run_mode: str
    adapter_status: str
    ready_to_run: bool
    command: str
    blocker: str
    adapter_module: str
    adapter_class: str
    adapter_implementation_status: str
    checkpoint_exists: bool
    adapter_importable: bool
    missing_python_modules: tuple[str, ...]
    missing_files: tuple[str, ...]


DISPATCHER = "run_vln_native_eval.py"
DEFAULT_NAVDP_MISSION_SOURCE = (
    Path("/Users/dongjk/ProjectFiles/Navdp_Datagen_Pathplanner") / "tmp/mission_examples"
)
GN_BENCH_TOOLS = REPO_ROOT / "GN-Bench-Tools"
if str(GN_BENCH_TOOLS) not in sys.path:
    sys.path.insert(0, str(GN_BENCH_TOOLS))

ADAPTER_SPECS: dict[str, VLNAdapterSpec] = {
    "human_eval_json_policies": VLNAdapterSpec(
        model="human_eval_json_policies",
        runner="replay_cli",
        adapter_module="GN_Bench.human_eval.baseline_runner",
        adapter_class="POLICY_CLASSES",
        required_files=("eval_navdp_missions.py",),
        notes="Deterministic NavDP artifact replay baselines.",
    ),
    "GN-BAE": VLNAdapterSpec(
        model="GN-BAE",
        runner="gn0_bae_shell",
        adapter_module="bae_agent",
        adapter_class="BAEAgent",
        required_files=("eval_bae_InteriorGS.sh", "run.py"),
        notes="Existing GN0 Env runner shell entrypoint.",
    ),
    "FutureNav": VLNAdapterSpec(
        model="FutureNav",
        runner="python_adapter",
        adapter_module="vln_adapters.futurenav",
        adapter_class="FutureNavAdapter",
        implementation_status=ADAPTER_STATUS_STUB,
        required_python_modules=("torch", "transformers"),
        notes="FutureNav checkpoint can be fetched, but GN0 adapter is not implemented.",
    ),
    "AwareVLN": VLNAdapterSpec(
        model="AwareVLN",
        runner="python_adapter",
        adapter_module="vln_adapters.awarevln",
        adapter_class="AwareVLNAdapter",
        implementation_status=ADAPTER_STATUS_STUB,
        required_python_modules=("torch", "transformers"),
        notes="AwareVLN needs a GN0 observation/action wrapper.",
    ),
    "GA_VLN": VLNAdapterSpec(
        model="GA_VLN",
        runner="python_adapter",
        adapter_module="vln_adapters.ga_vln",
        adapter_class="GAVLNAdapter",
        implementation_status=ADAPTER_STATUS_STUB,
        required_python_modules=("torch", "transformers"),
        notes="GA-VLN needs RGB-D/BEV input mapping for GN0/NavDP.",
    ),
    "TIC_VLA": VLNAdapterSpec(
        model="TIC_VLA",
        runner="python_adapter",
        adapter_module="vln_adapters.tic_vla",
        adapter_class="TICVLAAdapter",
        implementation_status=ADAPTER_STATUS_STUB,
        required_python_modules=("torch",),
        notes="TIC-VLA checkpoint needs a GN0 low-level action wrapper.",
    ),
}


def assess_adapter(
    record: VLNModelRecord,
    *,
    mission_source: str | Path = DEFAULT_NAVDP_MISSION_SOURCE,
    result_path: str | Path = "tmp/vln_eval_plan",
    check_imports: bool = False,
) -> VLNAdapterReadiness:
    spec = adapter_spec_for(record)
    result_path = Path(result_path)
    command = _dispatcher_command(record.model, mission_source, result_path)
    checkpoint_exists = _local_target_exists(record.local_target)
    missing_files = tuple(path for path in spec.required_files if not (REPO_ROOT / path).exists())
    missing_python_modules = (
        _missing_python_modules(spec.required_python_modules) if check_imports else ()
    )
    adapter_importable = (
        _adapter_importable(spec.adapter_module, spec.adapter_class)
        if spec.adapter_module and check_imports
        else False
    )
    implementation_status = _implementation_status(spec, check_imports)

    if spec.runner == "replay_cli":
        blocker = _join_blockers(
            _missing_files_blocker(missing_files),
            _missing_modules_blocker(missing_python_modules),
        )
        return VLNAdapterReadiness(
            model=record.model,
            run_mode="json_policy_replay",
            adapter_status="ready" if not blocker else "missing_runtime",
            ready_to_run=not blocker,
            command=command,
            blocker=blocker,
            adapter_module=spec.adapter_module,
            adapter_class=spec.adapter_class,
            adapter_implementation_status=implementation_status,
            checkpoint_exists=True,
            adapter_importable=adapter_importable,
            missing_python_modules=missing_python_modules,
            missing_files=missing_files,
        )

    if spec.runner == "gn0_bae_shell":
        blocker = _join_blockers(
            _missing_files_blocker(missing_files),
            "" if checkpoint_exists else f"missing local checkpoint target: {record.local_target}",
            _missing_modules_blocker(missing_python_modules),
        )
        return VLNAdapterReadiness(
            model=record.model,
            run_mode="native_gn0_bae",
            adapter_status="existing_gn0_runner",
            ready_to_run=not blocker,
            command=command,
            blocker=blocker,
            adapter_module=spec.adapter_module,
            adapter_class=spec.adapter_class,
            adapter_implementation_status=implementation_status,
            checkpoint_exists=checkpoint_exists,
            adapter_importable=adapter_importable,
            missing_python_modules=missing_python_modules,
            missing_files=missing_files,
        )

    if record.needs_source_check:
        return _not_runnable(
            record,
            spec,
            command,
            run_mode="source_check_required",
            adapter_status="source_check_required",
            blocker="verify runnable code/checkpoint artifacts before scheduling",
            checkpoint_exists=checkpoint_exists,
            adapter_importable=adapter_importable,
            implementation_status=implementation_status,
            missing_python_modules=missing_python_modules,
            missing_files=missing_files,
        )

    if record.is_accelerator:
        return _not_runnable(
            record,
            spec,
            command,
            run_mode="accelerator_layer",
            adapter_status="attach_to_supported_native_model",
            blocker="not a standalone navigator",
            checkpoint_exists=checkpoint_exists,
            adapter_importable=adapter_importable,
            implementation_status=implementation_status,
            missing_python_modules=missing_python_modules,
            missing_files=missing_files,
        )

    if record.is_blocked:
        return _not_runnable(
            record,
            spec,
            command,
            run_mode="external_reported",
            adapter_status="blocked_by_checkpoint",
            blocker="no public runnable checkpoint/API source is available",
            checkpoint_exists=checkpoint_exists,
            adapter_importable=adapter_importable,
            implementation_status=implementation_status,
            missing_python_modules=missing_python_modules,
            missing_files=missing_files,
        )

    if record.can_schedule_native_eval:
        blocker = _join_blockers(
            _implementation_blocker(spec, implementation_status),
            "" if adapter_importable or not check_imports else _adapter_blocker(spec),
            "" if checkpoint_exists else f"missing local checkpoint target: {record.local_target}",
            _missing_files_blocker(missing_files),
            _missing_modules_blocker(missing_python_modules),
        )
        return VLNAdapterReadiness(
            model=record.model,
            run_mode="native_adapter",
            adapter_status="ready" if not blocker else "adapter_required",
            ready_to_run=not blocker,
            command=command,
            blocker=blocker,
            adapter_module=spec.adapter_module,
            adapter_class=spec.adapter_class,
            adapter_implementation_status=implementation_status,
            checkpoint_exists=checkpoint_exists,
            adapter_importable=adapter_importable,
            missing_python_modules=missing_python_modules,
            missing_files=missing_files,
        )

    return _not_runnable(
        record,
        spec,
        command,
        run_mode="blocked",
        adapter_status="blocked_by_checkpoint",
        blocker=f"unsupported checkpoint status: {record.checkpoint_status}",
        checkpoint_exists=checkpoint_exists,
        adapter_importable=adapter_importable,
        implementation_status=implementation_status,
        missing_python_modules=missing_python_modules,
        missing_files=missing_files,
    )


def adapter_spec_for(record: VLNModelRecord) -> VLNAdapterSpec:
    spec = ADAPTER_SPECS.get(record.model)
    if spec is not None:
        return spec
    return VLNAdapterSpec(
        model=record.model,
        runner="python_adapter",
        adapter_module=f"vln_adapters.{_safe_module_name(record.model)}",
        adapter_class=f"{_safe_class_name(record.model)}Adapter",
        implementation_status=ADAPTER_STATUS_MISSING,
        notes="Default placeholder for a future native Python adapter.",
    )


def summarize_readiness(rows: Iterable[VLNAdapterReadiness]) -> dict[str, object]:
    readiness = list(rows)
    return {
        "adapter_count": len(readiness),
        "ready_to_run_count": sum(1 for row in readiness if row.ready_to_run),
        "native_adapter_ready_count": sum(
            1
            for row in readiness
            if row.run_mode == "native_adapter" and row.ready_to_run
        ),
        "adapter_required_count": sum(
            1 for row in readiness if row.adapter_status == "adapter_required"
        ),
        "adapter_stub_count": sum(
            1
            for row in readiness
            if row.adapter_implementation_status == ADAPTER_STATUS_STUB
        ),
        "checkpoint_missing_count": sum(
            1
            for row in readiness
            if not row.checkpoint_exists and row.run_mode.startswith("native")
        ),
        "external_reported_count": sum(
            1 for row in readiness if row.run_mode == "external_reported"
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX_PATH))
    parser.add_argument("--model", action="append", default=[])
    parser.add_argument("--bucket")
    parser.add_argument("--mission-source", default=str(DEFAULT_NAVDP_MISSION_SOURCE))
    parser.add_argument("--result-root", default="tmp/vln_eval_plan")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of TSV.")
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Check Python imports for adapter modules and declared dependencies.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_model_matrix(args.matrix)
    if args.model:
        allowed = set(args.model)
        records = [record for record in records if record.model in allowed]
    if args.bucket:
        records = [record for record in records if record.bucket == args.bucket]

    rows = [
        assess_adapter(
            record,
            mission_source=args.mission_source,
            result_path=Path(args.result_root) / _safe_path_name(record.model),
            check_imports=args.check_imports,
        )
        for record in records
    ]

    if args.summary:
        print(json.dumps(summarize_readiness(rows), indent=2, sort_keys=True))
    elif args.json:
        print(json.dumps([asdict(row) for row in rows], indent=2, sort_keys=True))
    else:
        _print_tsv(rows)


def _not_runnable(
    record: VLNModelRecord,
    spec: VLNAdapterSpec,
    command: str,
    *,
    run_mode: str,
    adapter_status: str,
    blocker: str,
    checkpoint_exists: bool,
    adapter_importable: bool,
    implementation_status: str,
    missing_python_modules: tuple[str, ...],
    missing_files: tuple[str, ...],
) -> VLNAdapterReadiness:
    return VLNAdapterReadiness(
        model=record.model,
        run_mode=run_mode,
        adapter_status=adapter_status,
        ready_to_run=False,
        command=command,
        blocker=blocker,
        adapter_module=spec.adapter_module,
        adapter_class=spec.adapter_class,
        adapter_implementation_status=implementation_status,
        checkpoint_exists=checkpoint_exists,
        adapter_importable=adapter_importable,
        missing_python_modules=missing_python_modules,
        missing_files=missing_files,
    )


def _dispatcher_command(model: str, mission_source: str | Path, result_path: Path) -> str:
    return " ".join(
        shlex.quote(part)
        for part in (
            "python3",
            DISPATCHER,
            "--model",
            model,
            "--mission-source",
            str(mission_source),
            "--result-path",
            str(result_path),
        )
    )


def _adapter_importable(module_name: str, class_name: str) -> bool:
    try:
        module = importlib.import_module(module_name)
    except Exception:
        return False
    return hasattr(module, class_name)


def _implementation_status(spec: VLNAdapterSpec, check_imports: bool) -> str:
    if not check_imports:
        return spec.implementation_status
    try:
        module = importlib.import_module(spec.adapter_module)
        adapter_cls = getattr(module, spec.adapter_class)
    except Exception:
        return ADAPTER_STATUS_MISSING
    return str(
        getattr(
            adapter_cls,
            "IMPLEMENTATION_STATUS",
            getattr(module, "IMPLEMENTATION_STATUS", spec.implementation_status),
        )
    )


def _missing_python_modules(module_names: tuple[str, ...]) -> tuple[str, ...]:
    missing: list[str] = []
    for module_name in module_names:
        try:
            importlib.import_module(module_name)
        except Exception:
            missing.append(module_name)
    return tuple(missing)


def _local_target_exists(local_target: str) -> bool:
    if not local_target or local_target == "n/a":
        return False
    path = Path(local_target)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.exists()


def _missing_files_blocker(paths: tuple[str, ...]) -> str:
    if not paths:
        return ""
    return "missing runner files: " + ", ".join(paths)


def _missing_modules_blocker(modules: tuple[str, ...]) -> str:
    if not modules:
        return ""
    return "missing Python modules: " + ", ".join(modules)


def _adapter_blocker(spec: VLNAdapterSpec) -> str:
    return f"missing adapter implementation: {spec.adapter_module}:{spec.adapter_class}"


def _implementation_blocker(spec: VLNAdapterSpec, implementation_status: str) -> str:
    if implementation_status == ADAPTER_STATUS_NATIVE_READY:
        return ""
    if implementation_status == ADAPTER_STATUS_MISSING:
        return _adapter_blocker(spec)
    return (
        f"adapter implementation status is {implementation_status}: "
        f"{spec.adapter_module}:{spec.adapter_class}"
    )


def _join_blockers(*parts: str) -> str:
    return "; ".join(part for part in parts if part)


def _safe_module_name(value: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "_" for ch in value)
    return "_".join(part for part in safe.split("_") if part)


def _safe_class_name(value: str) -> str:
    return "".join(part.capitalize() for part in _safe_module_name(value).split("_"))


def _safe_path_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


def _print_tsv(rows: list[VLNAdapterReadiness]) -> None:
    import csv

    fieldnames = list(VLNAdapterReadiness.__dataclass_fields__)
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, delimiter="\t")
    writer.writeheader()
    for row in rows:
        writer.writerow(asdict(row))


if __name__ == "__main__":
    main()

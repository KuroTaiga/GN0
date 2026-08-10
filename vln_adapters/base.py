"""Base interfaces for native VLN model adapters.

Adapters should translate GN0/NavDP evaluation episodes into model-specific
inputs, run inference, and write native result artifacts under ``result_path``.
The lightweight dataclasses here deliberately avoid simulator-heavy imports so
adapter readiness can be checked on machines without GN_Bench runtime deps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


JsonDict = dict[str, Any]
ADAPTER_STATUS_NATIVE_READY = "native_ready"
ADAPTER_STATUS_STUB = "stub"
ADAPTER_STATUS_MISSING = "missing"


@dataclass(frozen=True)
class VLNAdapterContext:
    model: str
    model_path: Path
    mission_source: Path
    result_path: Path
    split: str = "mission_examples"
    options: JsonDict = field(default_factory=dict)


@dataclass(frozen=True)
class VLNObservation:
    episode_id: str
    instruction: str
    rgb: Any = None
    depth: Any = None
    topdown_map: Any = None
    pose: JsonDict = field(default_factory=dict)
    raw: JsonDict = field(default_factory=dict)


@dataclass(frozen=True)
class VLNAction:
    action: str
    waypoint: tuple[float, float] | None = None
    stop: bool = False
    raw: JsonDict = field(default_factory=dict)


@dataclass(frozen=True)
class VLNAdapterRunResult:
    result_path: Path
    summary_path: Path | None = None
    metrics: JsonDict = field(default_factory=dict)


class VLNModelAdapter(Protocol):
    """Protocol implemented by native model adapters."""

    def __init__(self, context: VLNAdapterContext) -> None:
        ...

    def reset(self, episode: JsonDict) -> None:
        ...

    def act(self, observation: VLNObservation) -> VLNAction:
        ...

    def run(self) -> VLNAdapterRunResult:
        ...


class AdapterNotImplementedError(NotImplementedError):
    """Raised by adapter stubs that document an integration target."""


class UnavailableVLNAdapter:
    """Base class for model-specific adapter placeholders.

    A subclass is useful when the model is tracked and has a planned GN0
    integration, but native observation/action mapping is not implemented yet.
    The registry treats these as importable but not runnable.
    """

    IMPLEMENTATION_STATUS = ADAPTER_STATUS_STUB
    MODEL_NAME = "unknown"
    MISSING_CAPABILITIES: tuple[str, ...] = ()

    def __init__(self, context: VLNAdapterContext) -> None:
        self.context = context

    def reset(self, episode: JsonDict) -> None:
        raise self._error()

    def act(self, observation: VLNObservation) -> VLNAction:
        raise self._error()

    def run(self) -> VLNAdapterRunResult:
        raise self._error()

    def _error(self) -> AdapterNotImplementedError:
        details = ", ".join(self.MISSING_CAPABILITIES) or "native GN0 adapter"
        return AdapterNotImplementedError(
            f"{self.MODEL_NAME} adapter is tracked but not runnable yet; missing {details}."
        )

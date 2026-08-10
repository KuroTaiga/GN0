"""TIC-VLA adapter placeholder for GN0/NavDP evaluation."""

from __future__ import annotations

from .base import UnavailableVLNAdapter


class TICVLAAdapter(UnavailableVLNAdapter):
    MODEL_NAME = "TIC-VLA"
    MISSING_CAPABILITIES = (
        "checkpoint loader",
        "dynamic-control state mapping",
        "low-level action bridge into GN_Bench",
    )

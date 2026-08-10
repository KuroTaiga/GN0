"""FutureNav adapter placeholder for GN0/NavDP evaluation."""

from __future__ import annotations

from .base import UnavailableVLNAdapter


class FutureNavAdapter(UnavailableVLNAdapter):
    MODEL_NAME = "FutureNav"
    MISSING_CAPABILITIES = (
        "checkpoint loader",
        "GN0 RGB/history observation mapping",
        "model action to GN_Bench action translation",
    )

"""AwareVLN adapter placeholder for GN0/NavDP evaluation."""

from __future__ import annotations

from .base import UnavailableVLNAdapter


class AwareVLNAdapter(UnavailableVLNAdapter):
    MODEL_NAME = "AwareVLN"
    MISSING_CAPABILITIES = (
        "checkpoint loader",
        "self-correction state mapping",
        "GN0 observation/action wrapper",
    )

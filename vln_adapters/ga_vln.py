"""GA-VLN adapter placeholder for GN0/NavDP evaluation."""

from __future__ import annotations

from .base import UnavailableVLNAdapter


class GAVLNAdapter(UnavailableVLNAdapter):
    MODEL_NAME = "GA-VLN"
    MISSING_CAPABILITIES = (
        "checkpoint loader",
        "RGB-D and BEV observation mapping",
        "geometry-action projection into GN_Bench",
    )

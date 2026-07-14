"""Packages what the GUI needs to show about the acoustic status."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from spear_mqtt_ctd.acoustic_health import AcousticPlausibilityResult


@dataclass(frozen=True)
class AcousticReadingStatus:
    plausible: bool
    reason: str | None
    received_at: datetime
    sample_pct: float | None = None
    chunk_pct: float | None = None
    adc_age_sec: float | None = None
    beamformer_age_sec: float | None = None

    @classmethod
    def from_result(
        cls,
        result: AcousticPlausibilityResult,
        received_at: datetime,
    ) -> AcousticReadingStatus:
        return cls(
            plausible=result.plausible,
            reason=result.reason,
            received_at=received_at,
            sample_pct=result.sample_pct,
            chunk_pct=result.chunk_pct,
            adc_age_sec=result.adc_age_sec,
            beamformer_age_sec=result.beamformer_age_sec,
        )

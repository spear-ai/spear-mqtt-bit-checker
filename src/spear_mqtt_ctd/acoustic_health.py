"""Acoustic Acsense/Beamformer plausibility checks (from BuoyStatus)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from spear_mqtt_ctd.acoustic_config import AcousticConfig


@dataclass(frozen=True)
class AcousticPlausibilityResult:
    plausible: bool
    reason: str | None = None
    sample_pct: float | None = None
    chunk_pct: float | None = None
    adc_age_sec: float | None = None
    beamformer_age_sec: float | None = None


def has_data(data: Any) -> bool:
    if data is None:
        return False
    stamp = getattr(data, "stamp", None)
    if stamp is None:
        return False
    seconds = int(getattr(stamp, "seconds", 0))
    nanos = int(getattr(stamp, "nanos", 0))
    return not (seconds == 0 and nanos == 0)


def _stamp_datetime(stamp: Any) -> datetime | None:
    if stamp is None:
        return None
    seconds = int(getattr(stamp, "seconds", 0))
    nanos = int(getattr(stamp, "nanos", 0))
    if seconds == 0 and nanos == 0:
        return None
    return datetime.fromtimestamp(seconds + nanos * 1e-9, tz=UTC)


def validate_acoustic(
    acsense_stats: Any,
    beamformer_stats: Any,
    *,
    now: datetime | None = None,
    config: AcousticConfig | None = None,
) -> AcousticPlausibilityResult:
    """Return whether Acsense + Beamformer stats look healthy."""
    cfg = config or AcousticConfig()

    if not has_data(acsense_stats):
        return AcousticPlausibilityResult(False, "no_adc_data")
    if not has_data(beamformer_stats):
        return AcousticPlausibilityResult(False, "no_beamformer_data")

    adc_stamp = _stamp_datetime(getattr(acsense_stats, "stamp", None))
    beamformer_stamp = _stamp_datetime(getattr(beamformer_stats, "stamp", None))
    if adc_stamp is None:
        return AcousticPlausibilityResult(False, "no_adc_stamp")
    if beamformer_stamp is None:
        return AcousticPlausibilityResult(False, "no_beamformer_stamp")

    reference = now or datetime.now(tz=UTC)
    adc_age_sec = (reference - adc_stamp).total_seconds()
    beamformer_age_sec = (reference - beamformer_stamp).total_seconds()

    if adc_age_sec > cfg.max_age_sec:
        return AcousticPlausibilityResult(
            False,
            "adc_stale",
            adc_age_sec=adc_age_sec,
            beamformer_age_sec=beamformer_age_sec,
        )
    if beamformer_age_sec > cfg.max_age_sec:
        return AcousticPlausibilityResult(
            False,
            "beamformer_stale",
            adc_age_sec=adc_age_sec,
            beamformer_age_sec=beamformer_age_sec,
        )

    adc_sps = float(getattr(acsense_stats, "samples_received_1sec", 0))
    lo = cfg.target_sps * (1.0 - cfg.sps_tolerance)
    hi = cfg.target_sps * (1.0 + cfg.sps_tolerance)
    if adc_sps < lo or adc_sps > hi:
        return AcousticPlausibilityResult(
            False,
            "adc_sps_out_of_range",
            adc_age_sec=adc_age_sec,
            beamformer_age_sec=beamformer_age_sec,
        )

    received = int(getattr(acsense_stats, "samples_received_total", 0))
    missed = int(getattr(acsense_stats, "samples_missed_total", 0))
    sample_total = received + missed
    if sample_total < cfg.min_total_samples:
        return AcousticPlausibilityResult(
            False,
            "settling_samples",
            adc_age_sec=adc_age_sec,
            beamformer_age_sec=beamformer_age_sec,
        )
    sample_pct = 100.0 * received / sample_total
    if sample_pct < cfg.min_sample_accept_pct:
        return AcousticPlausibilityResult(
            False,
            "low_sample_accept",
            sample_pct=sample_pct,
            adc_age_sec=adc_age_sec,
            beamformer_age_sec=beamformer_age_sec,
        )

    good = int(getattr(beamformer_stats, "chunks_good_total", 0))
    bad = int(getattr(beamformer_stats, "chunks_bad_total", 0))
    chunk_total = good + bad
    if chunk_total < cfg.min_total_chunks:
        return AcousticPlausibilityResult(
            False,
            "settling_chunks",
            sample_pct=sample_pct,
            adc_age_sec=adc_age_sec,
            beamformer_age_sec=beamformer_age_sec,
        )
    chunk_pct = 100.0 * good / chunk_total
    if chunk_pct < cfg.min_chunk_accept_pct:
        return AcousticPlausibilityResult(
            False,
            "low_chunk_accept",
            sample_pct=sample_pct,
            chunk_pct=chunk_pct,
            adc_age_sec=adc_age_sec,
            beamformer_age_sec=beamformer_age_sec,
        )

    return AcousticPlausibilityResult(
        True,
        sample_pct=sample_pct,
        chunk_pct=chunk_pct,
        adc_age_sec=adc_age_sec,
        beamformer_age_sec=beamformer_age_sec,
    )

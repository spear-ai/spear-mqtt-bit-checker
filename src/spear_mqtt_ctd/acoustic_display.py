"""GUI-friendly acoustic status display helpers (no ANSI escape codes)."""

from __future__ import annotations

from typing import Literal

from spear_mqtt_ctd.acoustic_status import AcousticReadingStatus

StatusLevel = Literal["green", "yellow", "red"]

YELLOW_REASONS = {
    "no_adc_data",
    "no_beamformer_data",
    "no_adc_stamp",
    "no_beamformer_stamp",
}


def acoustic_status_level(status: AcousticReadingStatus | None) -> StatusLevel:
    """Return green, yellow (no data), or red (implausible) for acoustic stats."""
    if status is None:
        return "yellow"
    if status.plausible:
        return "green"
    if status.reason in YELLOW_REASONS:
        return "yellow"
    return "red"


def acoustic_status_label(status: AcousticReadingStatus | None) -> str:
    """Short plain-text status label for tables."""
    if status is None:
        return "NO DATA"
    if status.plausible:
        return "PLAUSIBLE"
    if status.reason in YELLOW_REASONS:
        return f"WAITING: {status.reason}"
    return f"IMPLAUSIBLE ({status.reason or 'unknown'})"


def _format_pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.1f}%"


def acoustic_status_detail(status: AcousticReadingStatus | None) -> str:
    """Full status line for acoustic ADC + beamformer stats."""
    if status is None:
        return "WAITING: no acoustic stats yet"
    if status.plausible:
        return (
            f"PLAUSIBLE: samples {_format_pct(status.sample_pct)}, "
            f"chunks {_format_pct(status.chunk_pct)}"
        )
    reason = status.reason or "unknown"
    if reason in YELLOW_REASONS:
        return f"WAITING: {reason}"
    if reason == "adc_stale" and status.adc_age_sec is not None:
        return f"IMPLAUSIBLE (adc_stale): last ADC stats {int(status.adc_age_sec)}s ago"
    if reason == "beamformer_stale" and status.beamformer_age_sec is not None:
        age = int(status.beamformer_age_sec)
        return f"IMPLAUSIBLE (beamformer_stale): last beamformer stats {age}s ago"
    if reason == "low_sample_accept" and status.sample_pct is not None:
        return f"IMPLAUSIBLE (low_sample_accept): {_format_pct(status.sample_pct)} accepted"
    if reason == "low_chunk_accept" and status.chunk_pct is not None:
        return f"IMPLAUSIBLE (low_chunk_accept): {_format_pct(status.chunk_pct)} good"
    if reason == "adc_sps_out_of_range":
        return "IMPLAUSIBLE (adc_sps_out_of_range)"
    return f"IMPLAUSIBLE ({reason})"


def acoustic_status_metric_text(status: AcousticReadingStatus | None) -> str:
    """Metric column text, or '-' when no reading."""
    if status is None:
        return "-"
    if status.sample_pct is not None and status.chunk_pct is not None:
        return f"{status.sample_pct:.1f}% / {status.chunk_pct:.1f}%"
    if status.sample_pct is not None:
        return _format_pct(status.sample_pct)
    return "-"


def acoustic_detail_text_for_status(status: AcousticReadingStatus | None) -> str:
    """Detail column text; red failures show the reason."""
    if status is None:
        return acoustic_status_detail(None)
    if status.plausible:
        return ""
    return acoustic_status_detail(status)

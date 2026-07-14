"""Tests for acoustic GUI-friendly display helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from spear_mqtt_ctd.acoustic_display import (
    acoustic_detail_text_for_status,
    acoustic_status_detail,
    acoustic_status_label,
    acoustic_status_level,
    acoustic_status_metric_text,
)
from spear_mqtt_ctd.acoustic_status import AcousticReadingStatus


def _status(
    plausible: bool,
    *,
    reason: str | None = None,
    sample_pct: float | None = 99.5,
    chunk_pct: float | None = 99.8,
    adc_age_sec: float | None = None,
    beamformer_age_sec: float | None = None,
) -> AcousticReadingStatus:
    return AcousticReadingStatus(
        plausible=plausible,
        reason=reason,
        received_at=datetime.now(tz=UTC),
        sample_pct=sample_pct,
        chunk_pct=chunk_pct,
        adc_age_sec=adc_age_sec,
        beamformer_age_sec=beamformer_age_sec,
    )


def test_acoustic_status_level() -> None:
    assert acoustic_status_level(None) == "yellow"
    assert acoustic_status_level(_status(True)) == "green"
    assert acoustic_status_level(_status(False, reason="no_adc_data")) == "yellow"
    assert acoustic_status_level(_status(False, reason="adc_stale")) == "red"


def test_acoustic_status_label() -> None:
    assert acoustic_status_label(None) == "NO DATA"
    assert acoustic_status_label(_status(True)) == "PLAUSIBLE"
    assert acoustic_status_label(_status(False, reason="no_adc_data")) == "WAITING: no_adc_data"
    assert acoustic_status_label(_status(False, reason="low_sample_accept")) == (
        "IMPLAUSIBLE (low_sample_accept)"
    )


def test_acoustic_status_detail() -> None:
    assert acoustic_status_detail(None) == "WAITING: no acoustic stats yet"
    assert "PLAUSIBLE: samples 99.5%" in acoustic_status_detail(_status(True))
    assert acoustic_status_detail(_status(False, reason="no_adc_data")) == "WAITING: no_adc_data"
    assert "IMPLAUSIBLE (adc_stale): last ADC stats 142s ago" in acoustic_status_detail(
        _status(False, reason="adc_stale", adc_age_sec=142.0)
    )
    assert "IMPLAUSIBLE (low_sample_accept): 90.0% accepted" in acoustic_status_detail(
        _status(False, reason="low_sample_accept", sample_pct=90.0)
    )


def test_acoustic_status_metric_text() -> None:
    assert acoustic_status_metric_text(None) == "-"
    assert acoustic_status_metric_text(_status(True)) == "99.5% / 99.8%"


def test_acoustic_detail_text_for_status() -> None:
    assert acoustic_detail_text_for_status(None) == "WAITING: no acoustic stats yet"
    assert acoustic_detail_text_for_status(_status(True)) == ""
    assert "IMPLAUSIBLE (low_chunk_accept)" in acoustic_detail_text_for_status(
        _status(False, reason="low_chunk_accept", chunk_pct=90.0)
    )

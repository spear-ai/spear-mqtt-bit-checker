"""Tests for acoustic Acsense/Beamformer plausibility checks."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from spear_mqtt_ctd.acoustic_config import AcousticConfig
from spear_mqtt_ctd.acoustic_health import (
    AcousticPlausibilityResult,
    has_data,
    validate_acoustic,
)


def _stamp(*, age_sec: float = 0.0) -> MagicMock:
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
    reading_time = now - timedelta(seconds=age_sec)
    stamp = MagicMock()
    stamp.seconds = int(reading_time.timestamp())
    stamp.nanos = int((reading_time.timestamp() % 1) * 1e9)
    return stamp


def _acsense_stats(
    *,
    age_sec: float = 0.0,
    sps: float = 52000.0,
    received_total: int = 1000,
    missed_total: int = 0,
) -> MagicMock:
    stats = MagicMock()
    stats.stamp = _stamp(age_sec=age_sec)
    stats.samples_received_1sec = sps
    stats.samples_received_total = received_total
    stats.samples_missed_total = missed_total
    return stats


def _beamformer_stats(
    *,
    age_sec: float = 0.0,
    good_total: int = 100,
    bad_total: int = 0,
) -> MagicMock:
    stats = MagicMock()
    stats.stamp = _stamp(age_sec=age_sec)
    stats.chunks_good_total = good_total
    stats.chunks_bad_total = bad_total
    return stats


def test_has_data_false_for_zero_stamp() -> None:
    stats = MagicMock()
    stats.stamp.seconds = 0
    stats.stamp.nanos = 0
    assert has_data(stats) is False
    assert has_data(None) is False


def test_has_data_true() -> None:
    assert has_data(_acsense_stats()) is True


def test_plausible_stats() -> None:
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
    result = validate_acoustic(
        _acsense_stats(),
        _beamformer_stats(),
        now=now,
    )
    assert result == AcousticPlausibilityResult(
        True,
        sample_pct=100.0,
        chunk_pct=100.0,
        adc_age_sec=0.0,
        beamformer_age_sec=0.0,
    )


def test_no_adc_data() -> None:
    stats = MagicMock()
    stats.stamp.seconds = 0
    stats.stamp.nanos = 0
    result = validate_acoustic(stats, _beamformer_stats())
    assert result == AcousticPlausibilityResult(False, "no_adc_data")


def test_no_beamformer_data() -> None:
    stats = MagicMock()
    stats.stamp.seconds = 0
    stats.stamp.nanos = 0
    result = validate_acoustic(_acsense_stats(), stats)
    assert result == AcousticPlausibilityResult(False, "no_beamformer_data")


def test_adc_stale() -> None:
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
    result = validate_acoustic(
        _acsense_stats(age_sec=120.0),
        _beamformer_stats(),
        now=now,
        config=AcousticConfig(max_age_sec=90.0),
    )
    assert result.plausible is False
    assert result.reason == "adc_stale"
    assert result.adc_age_sec == 120.0


def test_beamformer_stale() -> None:
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
    result = validate_acoustic(
        _acsense_stats(),
        _beamformer_stats(age_sec=120.0),
        now=now,
        config=AcousticConfig(max_age_sec=90.0),
    )
    assert result.plausible is False
    assert result.reason == "beamformer_stale"
    assert result.beamformer_age_sec == 120.0


def test_adc_sps_out_of_range() -> None:
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
    result = validate_acoustic(
        _acsense_stats(sps=900.0),
        _beamformer_stats(),
        now=now,
    )
    assert result.plausible is False
    assert result.reason == "adc_sps_out_of_range"


def test_settling_samples() -> None:
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
    result = validate_acoustic(
        _acsense_stats(received_total=5, missed_total=0),
        _beamformer_stats(),
        now=now,
    )
    assert result.plausible is False
    assert result.reason == "settling_samples"


def test_low_sample_accept() -> None:
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
    result = validate_acoustic(
        _acsense_stats(received_total=90, missed_total=10),
        _beamformer_stats(),
        now=now,
    )
    assert result.plausible is False
    assert result.reason == "low_sample_accept"
    assert result.sample_pct == 90.0


def test_low_chunk_accept() -> None:
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
    result = validate_acoustic(
        _acsense_stats(),
        _beamformer_stats(good_total=90, bad_total=10),
        now=now,
    )
    assert result.plausible is False
    assert result.reason == "low_chunk_accept"
    assert result.chunk_pct == 90.0

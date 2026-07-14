"""Tests for stateful acoustic evaluator."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from spear_mqtt_ctd.acoustic_config import AcousticConfig
from spear_mqtt_ctd.acoustic_evaluator import AcousticEvaluator


def _stamp(*, age_sec: float = 0.0) -> MagicMock:
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
    reading_time = now - timedelta(seconds=age_sec)
    stamp = MagicMock()
    stamp.seconds = int(reading_time.timestamp())
    stamp.nanos = int((reading_time.timestamp() % 1) * 1e9)
    return stamp


def _acsense_stats(*, age_sec: float = 0.0, sps: float = 52000.0) -> MagicMock:
    stats = MagicMock()
    stats.stamp = _stamp(age_sec=age_sec)
    stats.samples_received_1sec = sps
    stats.samples_received_total = 1000
    stats.samples_missed_total = 0
    return stats


def _beamformer_stats(*, age_sec: float = 0.0) -> MagicMock:
    stats = MagicMock()
    stats.stamp = _stamp(age_sec=age_sec)
    stats.chunks_good_total = 100
    stats.chunks_bad_total = 0
    return stats


def test_evaluator_plausible() -> None:
    evaluator = AcousticEvaluator()
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
    status = evaluator.evaluate(_acsense_stats(), _beamformer_stats(), now=now)
    assert status.plausible is True
    assert status.sample_pct == 100.0
    assert status.chunk_pct == 100.0


def test_evaluator_low_sample_accept() -> None:
    evaluator = AcousticEvaluator()
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
    acsense = _acsense_stats()
    acsense.samples_received_total = 90
    acsense.samples_missed_total = 10
    status = evaluator.evaluate(acsense, _beamformer_stats(), now=now)
    assert status.plausible is False
    assert status.reason == "low_sample_accept"


def test_evaluator_reset_is_noop() -> None:
    evaluator = AcousticEvaluator(AcousticConfig(max_age_sec=90.0))
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
    evaluator.evaluate(_acsense_stats(), _beamformer_stats(), now=now)
    evaluator.reset()
    status = evaluator.evaluate(
        _acsense_stats(age_sec=120.0),
        _beamformer_stats(),
        now=now,
    )
    assert status.plausible is False
    assert status.reason == "adc_stale"

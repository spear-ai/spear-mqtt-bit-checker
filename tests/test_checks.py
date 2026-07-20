"""Tests for the standardized sensor check pipeline"""

from __future__ import annotations
from spear_mqtt_bit_checker.core import Frame, run_check
from spear_mqtt_bit_checker.registry import acoustic_spec, bno_spec, ctd_spec
from unittest.mock import MagicMock
from datetime import datetime, timedelta

#---- CTD Testing ----
#Creates cfg and Mock CTD Messages for tests to use
def _cfg():
    return {"min_temp_c": -6.0, "max_temp_c": 45.0, "max_age_sec": 60.0, "max_step_c": 2.0}

def _ctd_stale_msg(*, temp: float = 12.3, stamp=None):
    ctd = MagicMock()
    ctd.temperature = temp
    dt = datetime.now() - timedelta(seconds=95)

    ctd.stamp = MagicMock()
    ctd.stamp.seconds = int(dt.timestamp())
    ctd.stamp.nanos = int((dt.timestamp() % 1) * 1e9)
    return ctd

def _ctd_valid_msg(*, temp: float = 12.3, stamp=None):
    ctd = MagicMock()
    ctd.temperature = temp
    dt = datetime.now() - timedelta(seconds=20)

    ctd.stamp = MagicMock()
    ctd.stamp.seconds = int(dt.timestamp())
    ctd.stamp.nanos = int((dt.timestamp() % 1) * 1e9)
    return ctd

#Case CTD Sensor should be yellow for no_data
def test_yellow_ctd():
    frame = Frame()
    sensor_status = run_check(ctd_spec, frame)
    assert sensor_status.level == "yellow"
    assert sensor_status.reason == "no_data"
    assert not sensor_status.plausible

#Case CTD Sensor should be red for stale data
def test_red_stale():
    frame = Frame()
    frame.ctd = _ctd_stale_msg()
    sensor_status = run_check(ctd_spec, frame)
    assert sensor_status.level == "red"
    assert sensor_status.reason == "stale"
    assert not sensor_status.plausible

#Case CTD Sensor should be green
def test_green_ctd():
    frame = Frame()
    frame.ctd = _ctd_valid_msg()
    sensor_status = run_check(ctd_spec, frame)
    assert sensor_status.level == "green"
    assert sensor_status.reason == None
    assert sensor_status.plausible

#---- BNO Testing ----
#Mock BNO Message
def _bno_msg(
    *,
    age_sec: float = 20.0,
    offvert_range: float = 4.0,
    heading_range: float = 3.0,
    avg_dps: float = 1.0,
    accept_rate: float = 0.95,
):
    dt = datetime.now() - timedelta(seconds=age_sec)
    attitude = MagicMock()
    attitude.stamp = MagicMock()
    attitude.stamp.seconds = int(dt.timestamp())
    attitude.stamp.nanos = int((dt.timestamp() % 1) * 1e9)
    attitude.offvert_range_1min = offvert_range
    attitude.heading_range_1min = heading_range
    attitude.avg_dps_1min = avg_dps
    attitude.accept_rate_1min = accept_rate
    buoy_status = MagicMock()
    buoy_status.attitude_stats = attitude
    return buoy_status


#Case BNO Sensor should be yellow for no_data
def test_yellow_bno():
    frame = Frame() #None as buoy_status
    sensor_status = run_check(bno_spec, frame)
    assert sensor_status.level == "yellow"
    assert sensor_status.reason == "no_data"
    assert not sensor_status.plausible

#Case BNO Sensor should be red for stale data
def test_red_bno():
    frame = Frame()
    frame.buoy_status = _bno_msg(age_sec=95)
    sensor_status = run_check(bno_spec, frame)
    assert sensor_status.level == "red"
    assert sensor_status.reason == "stale"
    assert not sensor_status.plausible

#Case BNO Sensor should be green
def test_green_bno():
    frame = Frame()
    frame.buoy_status = _bno_msg()
    sensor_status = run_check(bno_spec, frame)
    assert sensor_status.level == "green"
    assert sensor_status.reason is None
    assert sensor_status.plausible

#---- Acoustic Testing ----
#Mock Acoustic Acsense + Beamformer Message
def _acsense_stats(
    *,
    age_sec: float = 20.0,
    sps: float = 52000.0,
    received_total: int = 1000,
    missed_total: int = 0,
):
    dt = datetime.now() - timedelta(seconds=age_sec)
    stats = MagicMock()
    stats.stamp = MagicMock()
    stats.stamp.seconds = int(dt.timestamp())
    stats.stamp.nanos = int((dt.timestamp() % 1) * 1e9)
    stats.samples_received_1sec = sps
    stats.samples_received_total = received_total
    stats.samples_missed_total = missed_total
    return stats


def _beamformer_stats(
    *,
    age_sec: float = 20.0,
    good_total: int = 100,
    bad_total: int = 0,
):
    dt = datetime.now() - timedelta(seconds=age_sec)
    stats = MagicMock()
    stats.stamp = MagicMock()
    stats.stamp.seconds = int(dt.timestamp())
    stats.stamp.nanos = int((dt.timestamp() % 1) * 1e9)
    stats.chunks_good_total = good_total
    stats.chunks_bad_total = bad_total
    return stats


def _acoustic_msg(
    *,
    acsense_age_sec: float = 20.0,
    beamformer_age_sec: float = 20.0,
    sps: float = 52000.0,
    received_total: int = 1000,
    missed_total: int = 0,
    good_total: int = 100,
    bad_total: int = 0,
):
    buoy_status = MagicMock()
    buoy_status.acsense_stats = _acsense_stats(
        age_sec=acsense_age_sec,
        sps=sps,
        received_total=received_total,
        missed_total=missed_total,
    )
    buoy_status.beamformer_stats = _beamformer_stats(
        age_sec=beamformer_age_sec,
        good_total=good_total,
        bad_total=bad_total,
    )
    return buoy_status


#Case Acoustic Sensor should be yellow for no_data
def test_yellow_acoustic():
    frame = Frame()
    sensor_status = run_check(acoustic_spec, frame)
    assert sensor_status.level == "yellow"
    assert sensor_status.reason == "no_data"
    assert not sensor_status.plausible


#Case Acoustic Sensor should be red for stale data
def test_red_acoustic():
    frame = Frame()
    frame.buoy_status = _acoustic_msg(acsense_age_sec=95)
    sensor_status = run_check(acoustic_spec, frame)
    assert sensor_status.level == "red"
    assert sensor_status.reason == "stale"
    assert not sensor_status.plausible


#Case Acoustic Sensor should be green
def test_green_acoustic():
    frame = Frame()
    frame.buoy_status = _acoustic_msg()
    sensor_status = run_check(acoustic_spec, frame)
    assert sensor_status.level == "green"
    assert sensor_status.reason is None
    assert sensor_status.plausible

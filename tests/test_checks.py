"""Tests for the standardized sensor check pipeline"""

from __future__ import annotations
from spear_mqtt_ctd.core import Frame, run_check
from spear_mqtt_ctd.registry import bno_spec, ctd_spec
from unittest.mock import MagicMock
from datetime import datetime, timedelta


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

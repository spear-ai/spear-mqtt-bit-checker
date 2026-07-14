"""Contains custom functions for each sensor that checks that the data meets criteria
When new sensors are added to BIT Test Tab, a function must be added for each."""
from __future__ import annotations
from datetime import UTC, datetime
from typing import Any
import math

from spear_mqtt_ctd.core import CheckResult, Frame
from spear_mqtt_ctd.parser import extract_temperature

#---- Function to convert time into Python ----
def _stamp_datetime(stamp: Any) -> datetime | None:
    if stamp is None:
        return None
    seconds = int(getattr(stamp, "seconds", 0))
    nanos = int(getattr(stamp, "nanos", 0))
    if seconds == 0 and nanos == 0:
        return None
    return datetime.fromtimestamp(seconds + nanos * 1e-9, tz=UTC)


#---- Function to validate CTD Temperature - outputs CheckResult Object ----
def check_ctd(
    frame: Frame, 
    cfg: dict[str, float]
    ) -> CheckResult:

    #no data in yet
    if frame.ctd is None:
        return CheckResult(
            plausible=False,
            reason="no_data",
            metrics = None
        )
    reading_time = _stamp_datetime(getattr(frame.ctd, "stamp", None))
    if reading_time is None:
        return CheckResult(
            plausible=False,
            reason="no_data",
            metrics = None
        )

    ctd_temperature = extract_temperature(frame.ctd)
    #check that it is finite
    if not math.isfinite(ctd_temperature):
        return CheckResult(
            plausible=False, 
            reason="not_finite", 
            metrics={"temp": ctd_temperature}
        )

    #check that it meets min_temp_c requirement
    if ctd_temperature <= cfg["min_temp_c"]:
        return CheckResult(
            plausible=False,
            reason="does_not_meet_min_temp_c",
            metrics = {"temp": ctd_temperature}
        )
    
    #check that it meets max_temp_c requirement
    if ctd_temperature >= cfg["max_temp_c"]:
        return CheckResult(
            plausible=False,
            reason="does_not_meet_max_temp_c",
            metrics = {"temp": ctd_temperature}
        )

    #check that it meets max_age_sec requirement / isn't stale
    if reading_time is not None:
        reference = datetime.now(tz=UTC)
        age_sec = (reference - reading_time).total_seconds()
        if age_sec > cfg["max_age_sec"]:
            return CheckResult(
            plausible=False,
            reason="stale",
            metrics = {"reading age": age_sec}
        )
    
    #check that max_step_c requirement is met
    if frame.state is None:
        frame.state = {}
    prev_temp = frame.state.get("prev_temp")
    if prev_temp is not None:
        if abs(prev_temp - ctd_temperature) >= cfg["max_step_c"]:
            return CheckResult(
            plausible=False,
            reason="unstable_temperature",
            metrics = {"temp": ctd_temperature}
        )
    frame.state["prev_temp"] = ctd_temperature

    return CheckResult(
        plausible=True,
        reason=None,
        metrics={"temp": ctd_temperature}
    )


#---- Function to validate BNO Attitude - outputs CheckResult Object ----
def check_bno(
    frame: Frame,
    cfg: dict[str, float],
) -> CheckResult:
    
    #no data in yet
    if frame.buoy_status is None:
        return CheckResult(
            plausible=False,
            reason="no_data",
            metrics = None
        )
    attitude = getattr(frame.buoy_status, "attitude_stats", None)
    if attitude is None:
        return CheckResult(
            plausible=False,
            reason="no_data",
            metrics = None
        )
    reading_time = _stamp_datetime(getattr(attitude, "stamp", None))
    if reading_time is None:
        return CheckResult(
            plausible=False,
            reason="no_data",
            metrics = None
        )

    #check if data is stale
    if reading_time is not None:
        reference = datetime.now(tz=UTC)
        age_sec = (reference - reading_time).total_seconds()
        if age_sec > cfg["max_age_sec"]:
            return CheckResult(
            plausible=False,
            reason="stale",
            metrics = {"reading age": age_sec}
        )

    #check degrees per second
    avg_dps = float(getattr(attitude, "avg_dps_1min", 0.0))
    if avg_dps > cfg["max_dps"]:
        return CheckResult(
            plausible=False,
            reason="exceeds_max_dps",
            metrics = {"avg_dps_1min": avg_dps}
        )
    
    #accept rate
    accept_rate = float(getattr(attitude, "accept_rate_1min", 0.0))
    if accept_rate < cfg["min_accept_rate"]:
        return CheckResult(
            plausible=False,
            reason="below_min_accept_rate",
            metrics = {"accept_rate": accept_rate}
        )
    
    #max_range_deg
    offvert = float(getattr(attitude, "offvert_range_1min", 0.0))
    heading = float(getattr(attitude, "heading_range_1min", 0.0))
    if max(offvert, heading) > cfg["max_range_deg"]:
        return CheckResult(
            plausible=False,
            reason="above_max_range_deg",
            metrics = {"degree_range": max(offvert, heading)}
        )
    
    return CheckResult(
        plausible=True,
        reason=None,
        metrics = {"degree_range": max(offvert, heading)}
    )

#---- Function to validate Acoustic Acsense and Beamformer - outputs CheckResult Object ----
def check_acoustic(
    frame: Frame,
    cfg: dict[str, float],
) -> CheckResult:

    #no data in yet
    if frame.buoy_status is None:
        return CheckResult(
            plausible=False,
            reason="no_data",
            metrics=None,
        )
    acsense = getattr(frame.buoy_status, "acsense_stats", None)
    beamformer = getattr(frame.buoy_status, "beamformer_stats", None)

    if acsense is None or beamformer is None:
        return CheckResult(
            plausible=False,
            reason="no_data",
            metrics=None,
        )
    reading_time_acsense = _stamp_datetime(getattr(acsense, "stamp", None))
    reading_time_beamformer = _stamp_datetime(getattr(beamformer, "stamp", None))

    if reading_time_acsense is None or reading_time_beamformer is None:
        return CheckResult(
            plausible=False,
            reason="no_data",
            metrics=None,
        )

    #check if data is stale
    reference = datetime.now(tz=UTC)
    ac_age_sec = (reference - reading_time_acsense).total_seconds()
    if ac_age_sec > cfg["max_age_sec"]:
        return CheckResult(
            plausible=False,
            reason="stale",
            metrics={"reading age": ac_age_sec},
        )

    beamformer_age_sec = (reference - reading_time_beamformer).total_seconds()
    if beamformer_age_sec > cfg["max_age_sec"]:
        return CheckResult(
            plausible=False,
            reason="stale",
            metrics={"reading age": beamformer_age_sec},
        )

    #samples per second check
    ac_sps = float(getattr(acsense, "samples_received_1sec", 0))
    lo = cfg["target_sps"] * (1.0 - cfg["sps_tolerance"])
    hi = cfg["target_sps"] * (1.0 + cfg["sps_tolerance"])
    if ac_sps < lo or ac_sps > hi:
        return CheckResult(
            plausible=False,
            reason="out_of_sps_range",
            metrics={"sps": ac_sps},
        )

    #check min_total_samples and min_sample_accept_pct
    received = int(getattr(acsense, "samples_received_total", 0))
    missed = int(getattr(acsense, "samples_missed_total", 0))
    sample_total = received + missed
    if sample_total < cfg["min_total_samples"]:
        return CheckResult(
            plausible=False,
            reason="settling_samples",
            metrics={"total samples": sample_total},
        )
    sample_pct = 100.0 * received / sample_total
    if sample_pct < cfg["min_sample_accept_pct"]:
        return CheckResult(
            plausible=False,
            reason="low_sample_accept",
            metrics={"sample_pct": sample_pct},
        )

    #check beamformer chunks
    good = int(getattr(beamformer, "chunks_good_total", 0))
    bad = int(getattr(beamformer, "chunks_bad_total", 0))
    chunk_total = good + bad
    if chunk_total < cfg["min_total_chunks"]:
        return CheckResult(
            plausible=False,
            reason="settling_chunks",
            metrics={"total chunks": chunk_total},
        )
    chunk_pct = 100.0 * good / chunk_total
    if chunk_pct < cfg["min_chunk_accept_pct"]:
        return CheckResult(
            plausible=False,
            reason="low_chunk_accept",
            metrics={"chunk_pct": chunk_pct},
        )

    return CheckResult(
        plausible=True,
        reason=None,
        metrics={"sample_pct": sample_pct, "chunk_pct": chunk_pct},
    )
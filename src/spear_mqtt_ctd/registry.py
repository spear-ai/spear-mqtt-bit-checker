"""Contains all available sensors as a SensorSpec Box per sensor"""

from __future__ import annotations

from spear_mqtt_ctd.checks import check_acoustic, check_bno, check_ctd
from spear_mqtt_ctd.core import SensorSpec

ctd_spec = SensorSpec(
    key="ctd_temp",
    name= "CTD temperature",
    default_threshold={"min_temp_c": -6.0, "max_temp_c": 45.0, "max_age_sec": 60.0, "max_step_c": 2.0},
    check_func=check_ctd,
    yellow_reasons=frozenset({"no_data"})
)

bno_spec = SensorSpec(
    key="bno_attitude",
    name= "BNO attitude",
    default_threshold={"max_age_sec": 90.0, "min_accept_rate": 0.6, "max_range_deg": 15.0, "max_dps": 100.0},
    check_func=check_bno,
    yellow_reasons=frozenset({"no_data"})
)

acoustic_spec = SensorSpec(
    key="acoustic_acsense_and_beamformer",
    name="Acoustic Acsense and Beamformer",
    default_threshold={
        "max_age_sec": 90.0,
        "target_sps": 52000.0,
        "sps_tolerance": 0.02,
        "min_total_samples": 10.0,
        "min_sample_accept_pct": 99.0,
        "min_total_chunks": 10.0,
        "min_chunk_accept_pct": 99.0,
    },
    check_func=check_acoustic,
    yellow_reasons=frozenset({"no_data", "settling_samples", "settling_chunks"}),
)
#add sensors here
SENSORS = [ctd_spec, bno_spec, acoustic_spec]
"""Contains all available sensors as a SensorSpec Box per sensor"""

from __future__ import annotations

from spear_mqtt_ctd.checks import check_bno, check_ctd
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

#add sensors here
SENSORS = [ctd_spec, bno_spec]
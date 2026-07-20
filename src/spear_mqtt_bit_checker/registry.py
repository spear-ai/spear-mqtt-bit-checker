"""Contains all available sensors as a SensorSpec Box per sensor"""

from __future__ import annotations

from spear_mqtt_bit_checker.checks import check_acoustic, check_bno, check_ctd
from spear_mqtt_bit_checker.core import SensorSpec

#Defines the defaults for the SensorSpecs
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


DEFAULTS = {
    "ctd_spec": ctd_spec,
    "bno_spec": bno_spec,
    "acoustic_spec": acoustic_spec
}

#sensors are added here
SENSORS = [ctd_spec, bno_spec, acoustic_spec]

#read any changes made in the sensor_config.yaml file and use defaults where no changes
#input is open and loaded yaml file
def load_sensors(config: dict[str, any]) -> list[SensorSpec]:
    SENSORS.clear()
    for sensor_name, sensor_data in DEFAULTS.items():
        #gets the yaml thresholds
        sensors_cfg = config.get("sensors", config)
        yaml_threshold = sensors_cfg.get(sensor_data.key, {}).get("thresholds", {}) or {}
        #makes a copy of the defaults threshold
        sensor_data_copy = DEFAULTS[sensor_name].default_threshold.copy()
        sensor_data_copy.update(yaml_threshold)
        #create new SensorSpec to hold the updates
        spec_copy = SensorSpec(
            key = sensor_data.key,
            name = sensor_data.name,
            default_threshold=sensor_data_copy,
            check_func = sensor_data.check_func,
            yellow_reasons = sensor_data.yellow_reasons
        )
        SENSORS.append(spec_copy)
    return SENSORS
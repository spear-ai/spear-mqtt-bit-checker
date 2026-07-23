"""Contains all available sensors as a SensorSpec Box per sensor"""

from __future__ import annotations

from typing import Any

from spear_mqtt_bit_checker.checks import check_acoustic, check_bno, check_ctd
from spear_mqtt_bit_checker.core import SensorSpec

# Sensor metadata (thresholds come only from YAML via load_sensors)
DEFAULTS = [
    {
        "key": "ctd_temp",
        "name": "CTD temperature",
        "check_func": check_ctd,
        "yellow_reasons": frozenset({"no_data"}),
    },
    {
        "key": "bno_attitude",
        "name": "BNO attitude",
        "check_func": check_bno,
        "yellow_reasons": frozenset({"no_data"}),
    },
    {
        "key": "acoustic_acsense_and_beamformer",
        "name": "Acoustic Acsense and Beamformer",
        "check_func": check_acoustic,
        "yellow_reasons": frozenset({"no_data", "settling_samples", "settling_chunks"}),
    },
]

# sensors are added here
SENSORS = []


# input is open and loaded yaml file
def load_sensors(config: dict[str, Any]) -> list[SensorSpec]:
    SENSORS.clear()
    sensors_cfg = config.get("sensors", config)

    for sensor_name in DEFAULTS:
        # gets the yaml thresholds
        yaml_threshold = sensors_cfg.get(sensor_name["key"], {}).get("thresholds")

        # Raise error if thresholds key is missing entirely in YAML
        if not yaml_threshold:
            raise KeyError(f"Missing thresholds block for sensor: {sensor_name['key']}")

        # Raise error if any individual value inside YAML is None/null
        for threshold in yaml_threshold:
            if yaml_threshold[threshold] is None:
                raise KeyError(
                    f"Missing threshold value for '{threshold}' in '{sensor_name['key']}'"
                )

        # create new SensorSpec to hold the updates
        spec_copy = SensorSpec(
            key=sensor_name["key"],
            name=sensor_name["name"],
            default_threshold=yaml_threshold,
            check_func=sensor_name["check_func"],
            yellow_reasons=sensor_name["yellow_reasons"],
        )
        SENSORS.append(spec_copy)

    return SENSORS

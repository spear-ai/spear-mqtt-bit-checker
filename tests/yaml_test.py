import yaml

from spear_mqtt_ctd.registry import load_sensors, DEFAULTS

from pathlib import Path

#Tests that sensors have the correct updated thresholds
def test_update():
    config_path = Path(__file__).parent / "test_config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    #list of the updated sensors
    updated_specs = load_sensors(config)
    sensors_cfg = config.get("sensors", config)
    for sensor in updated_specs:
        yaml_threshold = sensors_cfg.get(sensor.key, {}).get("thresholds", {})
        for criteria in yaml_threshold:
            assert sensor.default_threshold[criteria] == yaml_threshold[criteria]
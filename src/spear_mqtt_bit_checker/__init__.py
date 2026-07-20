"""Public API for spear-mqtt-bit-checker."""

from spear_mqtt_bit_checker.config import BrokerConfig, load_broker_config
from spear_mqtt_bit_checker.core import Frame, SensorStatus, run_check
from spear_mqtt_bit_checker.parser import (
    CTD_TOPIC_SUFFIX,
    CtdParseError,
    buoy_uuid_from_ctd_topic,
    extract_temperature,
    is_ctd_topic,
    parse_ctd_payload,
)
from spear_mqtt_bit_checker.registry import SENSORS, acoustic_spec, bno_spec, ctd_spec
from spear_mqtt_bit_checker.uuid import (
    BuoySelection,
    MonitorMode,
    build_buoy_serial,
    prompt_buoy_serial,
    prompt_monitor_mode,
    resolve_buoy_selection,
    resolve_monitor_mode,
    serial_to_buoy_uuid,
)

__all__ = [
    "BrokerConfig",
    "BuoySelection",
    "CTD_TOPIC_SUFFIX",
    "CtdParseError",
    "Frame",
    "MonitorMode",
    "SENSORS",
    "SensorStatus",
    "acoustic_spec",
    "bno_spec",
    "build_buoy_serial",
    "buoy_uuid_from_ctd_topic",
    "ctd_spec",
    "extract_temperature",
    "is_ctd_topic",
    "load_broker_config",
    "parse_ctd_payload",
    "prompt_buoy_serial",
    "prompt_monitor_mode",
    "resolve_buoy_selection",
    "resolve_monitor_mode",
    "run_check",
    "serial_to_buoy_uuid",
]

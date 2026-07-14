"""Public API for spear-mqtt-ctd."""

from spear_mqtt_ctd.acoustic_config import AcousticConfig
from spear_mqtt_ctd.acoustic_display import (
    acoustic_detail_text_for_status,
    acoustic_status_detail,
    acoustic_status_label,
    acoustic_status_level,
    acoustic_status_metric_text,
)
from spear_mqtt_ctd.acoustic_evaluator import AcousticEvaluator
from spear_mqtt_ctd.acoustic_health import (
    AcousticPlausibilityResult,
    has_data,
    validate_acoustic,
)
from spear_mqtt_ctd.acoustic_status import AcousticReadingStatus
from spear_mqtt_ctd.config import BrokerConfig, load_broker_config
from spear_mqtt_ctd.core import Frame, SensorStatus, run_check
from spear_mqtt_ctd.parser import (
    CTD_TOPIC_SUFFIX,
    CtdParseError,
    buoy_uuid_from_ctd_topic,
    extract_temperature,
    is_ctd_topic,
    parse_ctd_payload,
)
from spear_mqtt_ctd.registry import SENSORS, bno_spec, ctd_spec
from spear_mqtt_ctd.uuid import (
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
    "AcousticConfig",
    "AcousticEvaluator",
    "AcousticPlausibilityResult",
    "AcousticReadingStatus",
    "BrokerConfig",
    "BuoySelection",
    "CTD_TOPIC_SUFFIX",
    "CtdParseError",
    "Frame",
    "MonitorMode",
    "SENSORS",
    "SensorStatus",
    "acoustic_detail_text_for_status",
    "acoustic_status_detail",
    "acoustic_status_label",
    "acoustic_status_level",
    "acoustic_status_metric_text",
    "bno_spec",
    "build_buoy_serial",
    "buoy_uuid_from_ctd_topic",
    "ctd_spec",
    "extract_temperature",
    "has_data",
    "is_ctd_topic",
    "load_broker_config",
    "parse_ctd_payload",
    "prompt_buoy_serial",
    "prompt_monitor_mode",
    "resolve_buoy_selection",
    "resolve_monitor_mode",
    "run_check",
    "serial_to_buoy_uuid",
    "validate_acoustic",
]

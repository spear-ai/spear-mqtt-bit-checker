"""Defines CheckResult, Frame, SensorStatus, and SensorSpec Classes and contains run_check function."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

#CheckResult is an object containing plausibility, reason, and metrics
@dataclass(frozen=True)
class CheckResult:
    plausible: bool
    #reason and metrics contain None when plausible is true
    reason: str | None = None
    metrics: dict[str, float] | None = None

#Frame is an object containing the raw CTD and buoy_status data and keeps track of state if needed
@dataclass
class Frame:
    ctd: Any | None = None
    buoy_status: Any | None = None
    state: dict[str, Any] | None = None

#SensorStatus is an object that contains a level attribute in addition to CheckResult's attributes
@dataclass(frozen=True)
class SensorStatus:
    plausible: bool
    #reason and metrics contain None when plausible is true
    reason: str | None
    metrics: dict[str, float] | None
    level: str | None

#SensorSpec is a general object that describes a given sensor (any)
@dataclass(frozen=True)
class SensorSpec:
    key: str
    name: str
    default_threshold: dict[str, float]
    check_func: Callable
    yellow_reasons: frozenset[str] = frozenset()

#run_check takes Frame / incoming data and SensorSpec as input and outputs a SensorStatus
def run_check(
    sensor_spec: SensorSpec,
    frame: Frame,
) -> SensorStatus:
   
    cfg = sensor_spec.default_threshold
    
    #outputs a CheckResult and populates output_status accordingly
    check_result = sensor_spec.check_func(frame, cfg)
   
    if check_result.plausible:
        level = "green"
    else:
        if check_result.reason in sensor_spec.yellow_reasons:
            level = "yellow"
        else:
            level = "red"
    
    return SensorStatus(
        plausible=check_result.plausible,
        reason=check_result.reason,
        metrics=check_result.metrics,
        level=level
    )
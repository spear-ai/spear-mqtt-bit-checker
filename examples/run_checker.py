#!/usr/bin/env python3
"""Minimal example: run the CTD check pipeline on a host-decoded CTD-like object."""

from __future__ import annotations

from datetime import datetime, timezone
from importlib.resources import files
from unittest.mock import MagicMock

import yaml
from spear_mqtt_bit_checker import Frame, load_sensors, run_check


def _sample_ctd(*, temp_c: float = 12.3, age_sec: float = 5.0) -> MagicMock:
    """Build a CTD-like object with stamp + temperature (same shape as protobuf)."""
    dt = datetime.now(tz=timezone.utc).timestamp() - age_sec
    ctd = MagicMock()
    ctd.temperature = temp_c
    ctd.stamp = MagicMock()
    ctd.stamp.seconds = int(dt)
    ctd.stamp.nanos = int((dt % 1) * 1e9)
    return ctd


def main() -> None:
    config = yaml.safe_load(
        files("spear_mqtt_bit_checker")
        .joinpath("sensor_config.yaml")
        .read_text(encoding="utf-8")
    )
    ctd_spec = next(spec for spec in load_sensors(config) if spec.key == "ctd_temp")

    frame = Frame(ctd=_sample_ctd())
    status = run_check(ctd_spec, frame)
    print(f"level={status.level} plausible={status.plausible} reason={status.reason}")
    if status.metrics:
        print(f"metrics={status.metrics}")


if __name__ == "__main__":
    main()

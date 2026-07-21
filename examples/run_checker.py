#!/usr/bin/env python3
"""Minimal example: run the CTD check pipeline on a host-decoded CTD-like object."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from spear_mqtt_bit_checker import Frame, ctd_spec, run_check


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
    frame = Frame(ctd=_sample_ctd())
    status = run_check(ctd_spec, frame)
    print(f"level={status.level} plausible={status.plausible} reason={status.reason}")
    if status.metrics:
        print(f"metrics={status.metrics}")


if __name__ == "__main__":
    main()

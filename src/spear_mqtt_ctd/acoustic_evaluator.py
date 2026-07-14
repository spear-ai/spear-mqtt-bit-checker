"""Stateful AcousticEvaluator (no MQTT dependency)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from spear_mqtt_ctd.acoustic_config import AcousticConfig
from spear_mqtt_ctd.acoustic_health import validate_acoustic
from spear_mqtt_ctd.acoustic_status import AcousticReadingStatus


class AcousticEvaluator:
    """Evaluate Acsense + Beamformer stats from BuoyStatus for BIT display."""

    def __init__(self, config: AcousticConfig | None = None) -> None:
        self._config = config or AcousticConfig()

    @property
    def config(self) -> AcousticConfig:
        return self._config

    def reset(self) -> None:
        """Clear tracked state (call when switching buoys)."""

    def evaluate(
        self,
        acsense_stats: Any,
        beamformer_stats: Any,
        now: datetime | None = None,
    ) -> AcousticReadingStatus:
        """Evaluate acoustic stats and return structured status."""
        result = validate_acoustic(
            acsense_stats,
            beamformer_stats,
            now=now,
            config=self._config,
        )
        received_at = now or datetime.now(tz=UTC)
        return AcousticReadingStatus.from_result(result, received_at)

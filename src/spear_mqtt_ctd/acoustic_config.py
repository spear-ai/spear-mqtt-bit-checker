"""Configuration for acoustic data checks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AcousticConfig:
    # samples per second in a tunable range
    target_sps: float = 52000.0
    sps_tolerance: float = 0.02

    # Samples Total not less than 99%
    min_sample_accept_pct: float = 99.0

    # Chunk Total not less than 99%
    min_chunk_accept_pct: float = 99.0

    # Staleness
    max_age_sec: float = 90.0

    # Minimum number of samples and chunks to start judging - avoid skewed rates from initial settling
    min_total_samples: float = 10.0
    min_total_chunks: float = 10.0

# spear-mqtt-ctd

A standalone Python library that evaluates the plausibility of sensor telemetry published by Spear buoys — CTD (Conductivity, Temperature, Depth), BNO attitude, and Acsense/Beamformer acoustic stats — and classifies each reading as **green** (healthy), **yellow** (no data / not settled yet), or **red** (implausible).

It is designed to be embedded in a host application (e.g. a BIT — Built-In Test — dashboard or GUI) that already receives protobuf-decoded sensor messages, typically over MQTT from the Spear broker. This package does **not** open an MQTT connection or run a CLI itself; it provides the parsing, plausibility-check, and configuration building blocks that a host application wires together.

It is independent of the `edge-sensors` ROS/GUI codebase but reuses the same CTD protobuf schema, MQTT broker YAML config format, and buoy serial → UUID algorithm, so results are consistent between the two.

## What it does

- Deserializes `CtdSensor` protobuf payloads received on `devices/<buoy_uuid>/sensors/ctd`
- Runs each sensor's raw data through a plausibility check and returns a `SensorStatus` with a `green` / `yellow` / `red` level, a machine-readable reason code, and metrics
- Ships checks for two sensor types out of the box: CTD temperature and BNO attitude — see [`registry.py`](src/spear_mqtt_ctd/registry.py)
- Evaluates Acsense (ADC) + Beamformer acoustic health stats via a stateful `AcousticEvaluator`, with GUI-friendly label/detail helpers
- Loads Spear MQTT broker connection details from the same nested YAML shape used by `edge-sensors`
- Converts buoy serial numbers (`BEN001-0000-00002`) to the MQTT device UUIDs used in topic paths, and back, using the same UUID v5 algorithm as `edge-sensors`

## Architecture

```
core.py        Frame / SensorSpec / SensorStatus / CheckResult + run_check() — the generic pipeline
checks.py      check_ctd(), check_bno() — per-sensor plausibility logic
registry.py    ctd_spec, bno_spec, SENSORS — wires checks.py functions into SensorSpec objects
parser.py      CTD protobuf (de)serialization, topic helpers
acoustic_*.py  Separate pipeline for Acsense/Beamformer acoustic stats (config, checks, stateful
               evaluator, GUI status/display helpers) — not part of the core.py Frame/SensorSpec flow
config.py      Broker YAML loading (BrokerConfig)
uuid.py        Buoy serial <-> UUID conversion, interactive prompts for buoy/mode selection
```

A host application owns the MQTT connection, decodes protobuf messages into a `Frame`, and calls `run_check()` (or the acoustic evaluator) to get a status it can render.

## Requirements

- Python 3.10+
- `protoc` (Protocol Buffers compiler) — only needed to regenerate `ctd_pb2.py` from `proto/ctd.proto` when building from source

```bash
# Ubuntu
sudo apt install protobuf-compiler

# macOS
brew install protobuf
```

## Installation

```bash
git clone https://github.com/<your-org>/spear-mqtt-ctd-checker.git
cd spear-mqtt-ctd-checker
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

Development and tests:

```bash
pip install ".[test]"
pytest -v
```

## Usage

### Run the CTD check on a parsed message

```python
from spear_mqtt_ctd import Frame, ctd_spec, run_check

frame = Frame(ctd=parsed_ctd_sensor)   # a spear_mqtt_ctd.ctd_pb2.CtdSensor
status = run_check(ctd_spec, frame)

print(status.level, status.plausible, status.reason)
# e.g. "green" True None
# or   "red"   False "stale"
```

`examples/run_checker.py` has a minimal, runnable version of this with a mocked CTD message.

### Run every registered sensor check

```python
from spear_mqtt_ctd import SENSORS, run_check
from spear_mqtt_ctd.core import Frame

frame = Frame(ctd=parsed_ctd_sensor, buoy_status=parsed_buoy_status)

for spec in SENSORS:
    status = run_check(spec, frame)
    print(f"{spec.name}: {status.level} ({status.reason})")
```

`Frame.state` persists between calls on the same `Frame` instance — reuse one `Frame` per buoy across successive readings so step/rate checks (like the CTD `max_step_c` check) have a previous value to compare against.

### Parse a raw CTD protobuf payload

```python
from spear_mqtt_ctd import extract_temperature, is_ctd_topic, parse_ctd_payload

if is_ctd_topic(mqtt_topic):
    ctd = parse_ctd_payload(mqtt_payload_bytes)
    temperature_c = extract_temperature(ctd)
```

### Evaluate acoustic (Acsense + Beamformer) health

```python
from spear_mqtt_ctd import AcousticEvaluator

evaluator = AcousticEvaluator()  # or AcousticEvaluator(AcousticConfig(target_sps=52000.0))
status = evaluator.evaluate(acsense_stats, beamformer_stats)

print(status.plausible, status.reason, status.sample_pct, status.chunk_pct)
```

Render it for a GUI with the display helpers:

```python
from spear_mqtt_ctd import acoustic_status_label, acoustic_status_level

acoustic_status_level(status)  # "green" | "yellow" | "red"
acoustic_status_label(status)  # e.g. "PLAUSIBLE" / "IMPLAUSIBLE (adc_stale)"
```

### Load Spear MQTT broker config

Uses the same nested YAML format as `edge-sensors` (e.g. `~/.ros/mqtt-broker-spear-hivemq.yaml`):

```yaml
/**/*:
  ros__parameters:
    host: your-broker.example.com
    port: 8883
    user: mda-buoy
    pass: your-password
```

```python
from spear_mqtt_ctd import load_broker_config

config = load_broker_config("~/.ros/mqtt-broker-spear-hivemq.yaml")
print(config.host, config.port, config.user)
```

Do not commit credentials to git.

### Buoy serial ↔ UUID conversion

Serials follow `edge-sensors` naming: `{BEN|MDA}001-0000-{unit zero-padded to 5 digits}`.

```python
from spear_mqtt_ctd import build_buoy_serial, serial_to_buoy_uuid

serial = build_buoy_serial("MDA", "27")       # "MDA001-0000-00027"
buoy_uuid = serial_to_buoy_uuid(serial)        # UUID used in devices/<uuid>/sensors/ctd
```

`uuid.py` also provides interactive prompt helpers (`prompt_buoy_serial`, `prompt_monitor_mode`, `resolve_buoy_selection`, `resolve_monitor_mode`) for host applications that want to ask a user to pick a buoy or run mode on the terminal.

### Run tests (no broker or MQTT connection required)

```bash
pytest -v
```

On systems with ROS installed, pytest is preconfigured in `pyproject.toml` to avoid plugin conflicts (`-p no:launch_testing`).

## Plausibility rules

### CTD temperature (`ctd_spec`)

| Check | Reason code | Default |
|-------|-------------|---------|
| Data present with a valid stamp | `no_data` (yellow) | — |
| Finite temperature | `not_finite` | reject NaN/inf |
| Minimum seawater temperature | `does_not_meet_min_temp_c` | -6.0 °C |
| Maximum seawater temperature | `does_not_meet_max_temp_c` | 45.0 °C |
| Reading age | `stale` | max 60 s |
| Step from previous reading | `unstable_temperature` | max 2.0 °C (skipped on first reading) |

### BNO attitude (`bno_spec`)

| Check | Reason code | Default |
|-------|-------------|---------|
| Data present with a valid stamp | `no_data` (yellow) | — |
| Reading age | `stale` | max 90 s |
| Rotation rate | `exceeds_max_dps` | max 100 dps |
| Accept rate | `below_min_accept_rate` | min 0.6 |
| Off-vertical / heading range | `above_max_range_deg` | max 15° |

### Acoustic (Acsense + Beamformer)

| Check | Reason code | Default |
|-------|-------------|---------|
| ADC / beamformer data present | `no_adc_data`, `no_beamformer_data` (yellow) | — |
| ADC / beamformer stamp present | `no_adc_stamp`, `no_beamformer_stamp` (yellow) | — |
| Reading age | `adc_stale`, `beamformer_stale` | max 90 s |
| Sample rate | `adc_sps_out_of_range` | 52000 sps ± 2% |
| Minimum samples/chunks before judging | `settling_samples`, `settling_chunks` | 10 each |
| Sample accept rate | `low_sample_accept` | min 99% |
| Chunk accept rate | `low_chunk_accept` | min 99% |

All thresholds are configurable — pass a custom `dict` in place of `ctd_spec.default_threshold` / `bno_spec.default_threshold`, or a custom `AcousticConfig` to `AcousticEvaluator`.

## Environment variables

None. This library takes all configuration as explicit function/constructor arguments — broker credentials are loaded from a YAML file path you supply to `load_broker_config()`, and check thresholds are plain Python values (see `registry.py` and `AcousticConfig`). It does not read any values from the process environment.

## Project layout

```text
proto/ctd.proto                 # CTD protobuf schema (from edge-sensors)
src/spear_mqtt_ctd/
  core.py                       # Frame / SensorSpec / SensorStatus / CheckResult + run_check()
  checks.py                     # check_ctd(), check_bno()
  registry.py                   # ctd_spec, bno_spec, SENSORS
  parser.py                     # CTD protobuf (de)serialization, topic helpers
  acoustic_config.py            # AcousticConfig thresholds
  acoustic_health.py            # validate_acoustic() — Acsense/Beamformer plausibility
  acoustic_evaluator.py         # Stateful AcousticEvaluator
  acoustic_status.py            # AcousticReadingStatus
  acoustic_display.py           # GUI label/detail/level helpers (no ANSI codes)
  config.py                     # load_broker_config() — Spear MQTT broker YAML
  uuid.py                       # Serial <-> UUID conversion, interactive prompts
  ctd_pb2.py                    # Generated from proto/ctd.proto (do not edit by hand)
tests/                          # pytest unit tests
examples/run_checker.py         # Minimal example: parse + run_check on a mocked CTD message
```

## Relationship to edge-sensors

| Shared with edge-sensors | This project |
|--------------------------|--------------|
| `proto/ctd.proto` | Same message format |
| MQTT broker YAML | Same config path/shape |
| `serial_to_buoy_uuid` | Same algorithm |
| CTD seawater range -6°C to 45°C | Same default thresholds |

This repo does **not** require ROS or the Spear GUI to run.

## License

Proprietary — adjust as needed for your organization.

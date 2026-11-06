# Firmware V1 — Smart DC Energy Monitor

Target: **ESP32-DevKitC-32E**, Arduino-ESP32 framework, sensor over I²C.
Status: **calculation core compiled and tested on the host; application layer never compiled or flashed.**

## What has actually been run

| Item | Status |
|---|---|
| `src/core/*.cpp` compiled with g++ 14 (`-std=c++17 -Wall -Wextra`) | **done, no warnings** |
| `test/test_core.cpp` — 69 checks against 8 vector sets | **done, all pass** |
| `src/main.cpp` compiled for ESP32 | **not done — no ESP32 toolchain available here** |
| Flashed and run on a board | **not done — no board exists** |
| I²C communication with a real INA226 | **not done** |

## Layout

```
include/dcm/types.h        units, Status, Calibration, Sample, EnergyTotals
include/dcm/ina226.h       register map and decode declarations
include/dcm/integrator.h   energy accumulation and the missing-data policy
src/core/ina226.cpp        decode implementation (no I2C, portable)
src/core/integrator.cpp    trapezoidal accumulation, wrap-safe timing
src/main.cpp               Arduino application layer (I2C, serial CSV)
test/test_core.cpp         desktop test suite
test/vectors_generated.h   vectors generated from the documented policy
platformio.ini             env:esp32dev and env:native
```

## Build and test on a desktop (no hardware, no platform library)

```bash
g++ -std=c++17 -Wall -Wextra -I include -o /tmp/dcm_core_test src/core/*.cpp test/test_core.cpp
/tmp/dcm_core_test
```

Expected tail:

```
  69 checks · 0 failed
  PASS: firmware core arithmetic, decode, calibration and missing-data policy
  NOT TESTED HERE: I2C communication, sensor accuracy, timing on the board.
```

## Build for the board (not done here)

```bash
pio run -e esp32dev
pio run -e esp32dev -t upload
pio device monitor -b 115200
```

## Serial output

```
timestamp_ms,voltage_V,current_A,power_W,energy_Wh,status
10250,11.9982,0.25031,3.0032,0.008341,OK
```

`timestamp_ms` is milliseconds since boot. This design has **no real-time clock**,
so no wall-clock time or date is produced anywhere. Comment lines beginning with
`#` carry events that must not be hidden, such as an interval that was not
integrated.

## Design decisions worth arguing with

- **Current is derived from the shunt voltage and the known resistance**, not from
  the INA226 current register. That removes any dependence on the calibration
  register being written correctly, and makes the arithmetic visible in one place.
- **A missing or invalid sample costs two intervals** — the one ending at it and
  the one starting from it. The alternative (integrating across a stale reading)
  would silently invent energy; this policy loses a little energy instead, and
  counts what it lost.
- **A gap longer than 5 s is treated as missing data**, not as a long interval.
- **Millisecond timestamps are unsigned 32-bit**, so subtraction wraps correctly
  after 49.7 days. The host test includes a rollover case.
- **Float, not double, on the device**; doubles are used only inside the energy
  accumulator, where repeated addition needs the extra precision.

## Calibration

`dcm::Calibration` holds a gain and an offset per channel, applied as
`corrected = raw × gain + offset` in engineering units. The plan that produces
those four numbers is in `../verification/calibration-plan/calibration-plan.md`.
Until it is run, the defaults are the identity and the firmware reports
uncalibrated values — which is why no accuracy is claimed.

# Firmware build evidence

Recorded from an actual build in this environment, not from intent. Reproduce
with `pio run -e esp32dev` in this directory.

| Item | Value |
|---|---|
| Build command | `pio run -e esp32dev` |
| Result | **SUCCESS** |
| PlatformIO Core | 6.2.0 |
| Platform | espressif32 8.0.0 |
| Framework | framework-arduinoespressif32 4.30312.261024 |
| Toolchain | toolchain-xtensa-esp-elf 14.2.0+20260121 |
| Board definition | `esp32dev` (generic ESP32 Dev Module, Xtensa LX6, 240 MHz) |
| Tools | esptool 5.4.0 |
| Compiler warnings | none at `-Wall -Wextra` |
| Firmware binary | `firmware.bin`, 333 508 bytes |
| Flash use | 25.4 % of 1 310 720 bytes |
| RAM use | 7.2 % — 23 588 bytes of 327 680 |
| First compile attempt | **failed**: `expected '}' at end of input`, and `setup()`/`loop()` reported unused because they were inside an anonymous namespace |
| Fix | closed the namespace before the Arduino entry points, giving them external linkage |

## What this proves, and what it does not

**Proves:** the code compiles for the selected architecture and board with the
stated toolchain, links against the Arduino-ESP32 core and the Wire library, and
fits comfortably in flash and RAM.

**Does not prove:** that the firmware runs, that I²C works on the board, that the
sensor is detected, or that any measurement is correct. **No ESP32 has been
connected to this project.** The binary was never flashed.

## Host test evidence (separate from the build)

```
g++ -std=c++17 -Wall -Wextra -I include -o /tmp/t src/core/*.cpp test/test_core.cpp
  → 69 checks · 0 failed
g++ -std=c++17 -Wall -Wextra -I include -o /tmp/s src/core/*.cpp test/test_sensor.cpp
  → 29 checks · 0 failed      (mocked I²C bus, not a sensor)
node ../tests/vector-model-parity.test.js
  → 20 checks · 0 failed      (vectors vs the verified JavaScript model)
```

# Bill of materials — DCM-HW-V1 rev A

Generated from `design/dcm-hw-v1.json` by `design/generate.py`; the machine-readable
version is `dcm-hw-v1-bom.csv`.

**No price is listed.** No supplier was queried in the authoring environment, and an
invented price is worse than an empty field. Nothing here has been purchased.

| Ref | Value | Part | Function | Key ratings |
|---|---|---|---|---|
| J1 | 2-way 5.08 mm | Phoenix MKDS 1/2-5.08 (or equivalent) | DC input terminals | 10 A, 300 V |
| F1 | 1.1 A hold / 2.2 A trip | Bourns MF-R110 | Resettable series protection | 1.1 A hold, 2.2 A trip, 60 V |
| D1 | 3 A 40 V Schottky | onsemi SS34 | Reverse-polarity protection | 3 A, 40 V |
| D2 | 15 V standoff 600 W | Littelfuse SMBJ15A | Transient clamp | 15 V standoff, 24.4 V clamp |
| R1 | 0.1 Ω 0.5 % 1 W | Vishay CRCW2512 0R1 | Current shunt | 0.1 Ω, 1 W, 100 ppm/°C |
| U1 | INA226 module | INA226 breakout (CJMCU-226 class) | Bus voltage and shunt current | 0–36 V bus, ±81.92 mV shunt, 2.7–5.5 V supply |
| U2 | ESP32-DevKitC-32E | Espressif | Microcontroller | 3.3 V logic |
| C1 | 10 µF 25 V X7R 1210 | Murata GRM32ER71E106KA12 | Bulk decoupling | 25 V |
| C2 | 100 nF 25 V X7R 0603 | KEMET C0603C104K3RAC | HF decoupling | 25 V |
| R2, R3 | 4.7 kΩ 1 % | Yageo RC0603FR-074K7L | I²C pull-ups to 3.3 V | 2× |
| J2 | 2-way 5.08 mm | Phoenix MKDS 1/2-5.08 (or equivalent) | Load output terminals | 10 A, 300 V |
| J3 | 4-way 2.54 mm header | Würth 61300411121 (or generic) | I²C + 3.3 V link to the MCU | 3 A |
| TP1–TP5 | Test points | Keystone 5000 series or 1 mm pads | Probe access | 5× |

## Besides the BOM you need

- One low-voltage DC bench supply with an adjustable current limit (≤ 1 A).
- Assorted power resistors as loads, rated for the dissipation: 12 Ω at 12 V is
  12 W, so use a 10 W part or several in series/parallel.
- A multimeter. Two is better: one for the circuit, one for the reference reading.
- A breadboard or a stripboard for the carrier, and hook-up wire.
- Optional but recommended: a USB current/voltage meter as a rough second opinion,
  and a logic analyser for the I²C bus.

## Substitutions that are fine, and ones that are not

- **Fine:** a different 5.08 mm terminal block of equal or greater rating; a
  different 4.7 kΩ 1 % resistor; a different 25 V X7R capacitor of the same value.
- **Not fine without redoing the numbers:** any different shunt value (the current
  range and calibration both change), any TVS with a lower standoff than 12 V, any
  Schottky rated below 40 V, and any INA226 module whose pull-ups are on 5 V.

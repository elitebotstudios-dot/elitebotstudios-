# Calibration and measurement verification plan — DCM-HW-V1

**No calibration has been performed.** Every table below is empty on purpose:
this is the procedure and the recording sheet, not a result. Filling it in
requires the built hardware and a reference instrument.

## 1. What calibration is for

The sensor returns a shunt voltage and a bus voltage. The firmware converts them
with nominal constants (2.5 µV per shunt LSB, 1.25 mV per bus LSB) and a 0.1 Ω
shunt. Every real system differs from that nominal model because of:

- shunt tolerance (this design uses 0.5 %, so ±0.5 % before anything else),
- amplifier gain error and offset inside the sensor,
- the actual shunt resistance after soldering and thermal cycling,
- voltage-divider tolerance if one is used (this design measures the bus directly),
- noise and quantisation.

Calibration measures those combined errors at known points and stores two
corrections per channel:

```
corrected = raw_reading × gain + offset
```

## 2. Reference instrument requirements

| Property | Requirement | Why |
|---|---|---|
| DC voltage accuracy | better than 0.1 % of reading | must be at least 10× better than the ±1 % target |
| DC current accuracy | better than 0.2 % of reading | 10× better than the ±2 % target |
| Resolution | 1 mV, 100 µA or better | to resolve the correction |
| Calibrated | within its own calibration interval | an uncalibrated reference is an opinion |
| Range | 0–15 V, 0–1 A | covers the envelope with headroom |

A bench multimeter (6.5 digits class) or an instrument with a current calibration
certificate. **A second multimeter of the same type is not a reference.**

## 3. Measurement conditions to record every time

Ambient temperature, supply voltage, load resistance, warm-up time, the
instrument used for each reading, and the firmware build. A number without its
conditions cannot be compared with anything later.

## 4. Procedure

### Stage 1 — Unpowered checks
1. Continuity from J1 pin 1 through F1, D1, R1 to J2 pin 1; expect a few ohms.
2. Continuity from J1 pin 2 to J2 pin 2 and to the module GND.
3. No continuity between VPROT and GND (a short here destroys the TVS and possibly the sensor).
4. Confirm D1 orientation and D2 orientation against the drawing.
5. Confirm the module pull-up rail question (design review Q2) before connecting 3.3 V.

Record: pass/fail per check, with the resistance measured.

### Stage 2 — Supervised power-up
1. Bench supply at 5 V, **current limit 100 mA**, no load connected.
2. Measure VPROT and VLOAD with the reference meter. Expect VLOAD ≈ VPROT − 0.05 V
   or less (no load → no shunt drop) and ≈ supply − diode drop.
3. Measure the 3V3 rail at J3 pin 1 after the ESP32 is connected. Expect 3.3 V ± 5 %.
4. Check the module does not get warm.

### Stage 3 — Communication
1. Run an I²C scan at 0x40. Record the address found.
2. Read the manufacturer and die ID registers; INA226 returns 0x5449 and 0x2260.
3. Confirm a bus reading that tracks the supply and a shunt reading near zero.

### Stage 4 — Known loads (no reference meter yet)
1. 12 Ω at 12 V (≈1 A — **do not use yet**, exceeds the 0.5 A envelope).
2. Use 100 Ω at 12 V (≈120 mA) and 47 Ω (≈255 mA), both within the envelope.
3. Record voltage, current, power and the energy after exactly 5 minutes.

### Stage 5 — Reference comparison
For each point: set the load, let it stabilise, read the reference meter and the
firmware **at the same moment**, and record both. Six points minimum, spanning the
range: 5 V and 12 V, at roughly 10 %, 25 %, 50 % of the 0.5 A envelope.

### Stage 6 — Deviation analysis
Compute the error at each point, as a percentage of reading. Separate:
- a constant offset (near-zero current reading, zero-load offset),
- a proportional gain error (error grows with reading),
- noise (repeat readings at one point, compute standard deviation).

### Stage 7 — Apply corrections
Set `voltage_gain`, `voltage_offset_v`, `current_gain`, `current_offset_a` from the
fit, reflash, and repeat Stage 5. Record both the pre- and post-calibration tables.

### Stage 8 — Uncertainty statement
State the residual error at each point after calibration, the repeatability, and
the conditions. If a point is worse than the target, say so and explain it.

## 5. Recording sheet

Copy `bench-test-template.csv` for each session. The columns are fixed:

```
stage,test_point,load_ohm,supply_v,ref_voltage_v,ref_current_a,dut_voltage_v,dut_current_a,
dut_power_w,energy_wh_after_5min,ambient_c,instrument,date,operator,pass,notes
```

A row with an unexplained failure is more valuable than a table of passing rows:
it is the only thing that tells the next person where the design is weak.

## 6. What will not be claimed after calibration

- Accuracy outside 5–12 V and 0–0.5 A.
- Long-term stability: one calibration session is a snapshot, not a drift study.
- Temperature behaviour: unless the tests are repeated at more than one ambient
  temperature, nothing is known about it.
- Anything about AC, isolation, or the model's simulated sensing chain being
  "equivalent" to the real one.

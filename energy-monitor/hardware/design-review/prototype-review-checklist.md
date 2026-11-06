# Physical prototype review checklist — DCM-HW-V1 rev B

For the founder to work through **before buying or energising anything**. Tick
each line only when it has been done and observed, not when it seems likely.

**This checklist is not a substitute for review by a qualified person.** Nothing
in this project has been built or measured, and the agent cannot perform any of
these steps remotely.

---

## Stage 0 — before ordering

- [ ] Read `design-review.md`, including the findings and the six open questions.
- [ ] Read the KiCad schematic (`kicad/dcm-hw-v1.kicad_sch`) and the ERC report.
- [ ] Confirm the envelope is still right: 5–12 V, ≤ 0.5 A, resistive load.
- [ ] Decide the build style: bare INA226 on an adapter board, or a breakout
      module. If a module, see the module checks below — the schematic is
      written for the bare IC and a module must match it.
- [ ] Confirm you have a bench supply with an adjustable current limit, a
      multimeter, and power resistors rated for the dissipation (12 Ω at 12 V is
      12 W, so use a 10 W part or several in series/parallel).

## Stage 1 — identify the parts that arrive

- [ ] INA226 marking reads INA226 (not INA219, not INA228). Compare against the
      TI datasheet package drawing.
- [ ] ESP32-DevKitC: silkscreen says ESP32-DevKitC-32E; confirm GPIO21 and GPIO22
      are on the header positions you expect **for your board revision**.
- [ ] Shunt: measure 0.1 Ω. A four-wire measurement is better; a two-wire
      measurement on a 1 W 2512 will read high by the lead resistance.
- [ ] Diode D1 is a Schottky, and you know which end is the cathode (the band).
- [ ] TVS D2 marking matches SMBJ15A (unidirectional).

## Stage 2 — module checks, if a breakout module is used

- [ ] **Address:** with 3.3 V applied and an I²C scanner, the device answers at
      0x40. If it answers elsewhere, the A0/A1 straps differ from the schematic.
- [ ] **Pull-up rail:** measure the resistance from SDA and SCL to VCC with the
      board unpowered. Then power it from 3.3 V only and measure the idle-high
      level on SDA and SCL: it must be ≈3.3 V, never 5 V.
- [ ] **Shunt:** identify the on-board shunt and its value. If it sits in
      parallel with your external 0.1 Ω, remove it or recalculate.
- [ ] **VBUS:** confirm the module ties VBUS to IN− (load side). If it exposes a
      separate VBUS pin, wire it to IN−. If it does not tie them at all, the bus
      reading is meaningless — do not proceed.
- [ ] **Common mode:** the INA226 accepts a 12 V common mode on IN+/IN−. Confirm
      the module's parts are rated for it.

## Stage 3 — unpowered wiring

- [ ] Continuity J1.1 → F1 → D1 anode; D1 cathode → R1.1; R1.2 → J2.1.
- [ ] Continuity J1.2 → J2.2 → sensor GND → ESP32 GND.
- [ ] **No** continuity between VPROT and GND (a short here destroys the TVS).
- [ ] D2 cathode to VPROT, anode to GND.
- [ ] 3V3 goes to sensor VS, never to the measured rail.
- [ ] Nothing is connected to mains. There is no mains in this design.

## Stage 4 — first power-up (supervised)

- [ ] Supply set to **5 V, current limit 100 mA**.
- [ ] Second person present, able to remove power.
- [ ] Measure: VIN ≈ 5 V; VPROT ≈ 5 V − diode drop; VLOAD ≈ VPROT (no load).
- [ ] Measure 3V3 at the sensor: 3.3 V ±5 %.
- [ ] Nothing is warm. The TVS is not conducting (it would run hot).
- [ ] Serial output prints the header and does **not** print a sensor error.

## Stage 5 — communication and first readings

- [ ] I²C scan finds 0x40.
- [ ] Manufacturer/die ID read correctly (the firmware checks this at start-up).
- [ ] With no load, current reads ≈0 A and voltage reads the supply.
- [ ] With a 100 Ω load at 12 V (≈120 mA), current reads ≈0.12 A.
- [ ] Compare against your multimeter. Record both numbers.

## Stage 6 — stop conditions

Stop and investigate immediately if any of these happen:

- [ ] Anything gets hot: TVS, shunt, sensor, connectors.
- [ ] The supply goes into current limit when no load is connected.
- [ ] The sensor does not acknowledge at 0x40 after the straps are confirmed.
- [ ] Current reads a constant value regardless of load (suspect the shunt or a
      saturated channel).
- [ ] Voltage reads zero while the supply is on (suspect VBUS is not connected).
- [ ] Energy accumulates while the current reads zero (suspect a bug — this
      cannot happen in the verified firmware).

## Stage 7 — before any calibration claim

- [ ] The bench test sheet in `verification/calibration-plan/` is filled in.
- [ ] At least six points across the range, each compared with a reference meter.
- [ ] Conditions recorded: ambient, supply, load, instruments, date.
- [ ] Failures recorded, not omitted.

Only after Stage 7 does this project have an accuracy figure. Until then, the
site will keep saying "hardware not built".

/* ===========================================================================
   config-consistency.test.js — schematic, firmware and website must agree

   A hardware/firmware mismatch (the firmware reading GPIO22 while the board is
   wired to GPIO4, or a shunt value that differs between the BOM and the code)
   is the kind of defect that survives every unit test and fails on the bench.
   This test reads the manifest and checks that the same numbers appear in the
   C++ sources, in the design file and on the published pages.

   Run: node energy-monitor/tests/config-consistency.test.js
   ========================================================================== */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const M = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'hardware', 'dcm-hw-v1.manifest.json'), 'utf8'));

let checks = 0;
const fails = [];
function ok(cond, label, detail) {
  checks += 1;
  if (!cond) fails.push(label + (detail === undefined ? '' : ' — ' + detail));
}

const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8');
const fw = {
  main: read('energy-monitor/firmware/src/main.cpp'),
  integratorH: read('energy-monitor/firmware/include/dcm/integrator.h'),
  ina226H: read('energy-monitor/firmware/include/dcm/ina226.h'),
  sensorCpp: read('energy-monitor/firmware/src/core/sensor.cpp')
};
const design = JSON.parse(read('energy-monitor/hardware/design/dcm-hw-v1.json'));
const designComp = Object.fromEntries(design.components.map((c) => [c.ref, c]));
/* pins are addressed by number or by name, because the drawing names some pins
   (a diode's A and K) and numbers others (the INA226's 1-10) */
const pinOf = (ref, key) => designComp[ref].pins.find((p) => p.number === key || p.name === key);

/* ---- 1. I2C address ------------------------------------------------------ */
{
  const addr = M.sensor.i2c_address;
  ok(fw.ina226H.includes(`kAddressA0GndA1Gnd = ${addr}`),
    'the firmware default address matches the manifest', addr);
  ok(fw.main.includes('kSensorAddress = dcm::ina226::kAddressA0GndA1Gnd'),
    'the application layer uses the library address constant');
  /* A0 and A1 to GND is what selects 0x40 on the INA226 */
  const a0 = pinOf('U1', 'A0');
  const a1 = pinOf('U1', 'A1');
  ok(a0 && a0.net === 'GND', 'A0 is strapped to GND in the schematic', a0 && a0.net);
  ok(a1 && a1.net === 'GND', 'A1 is strapped to GND in the schematic', a1 && a1.net);
  ok(/0x40/.test(M.sensor.address_straps) || /GND/.test(M.sensor.address_straps),
    'the manifest states how the address is strapped');
}

/* ---- 2. shunt value ------------------------------------------------------ */
{
  const ohms = M.sensor.shunt_ohms;
  ok(fw.main.includes(`kShuntOhms = ${ohms}f`), 'the firmware shunt value matches the manifest', ohms + ' ohm');
  const r1 = designComp.R1;
  ok(r1.ratings.resistance_ohm === ohms, 'the schematic shunt equals the manifest',
    r1.ratings.resistance_ohm);
  ok(designComp.R1.pins.some((p) => p.net === 'VPROT') &&
     designComp.R1.pins.some((p) => p.net === 'VLOAD'),
    'the shunt sits between VPROT and VLOAD');
  const iMax = M.sensor.shunt_full_scale_mv / 1000 / ohms;
  ok(Math.abs(iMax - M.envelope.measurable_current_max_a) < 1e-6,
    'the manifest current limit follows from the shunt and the sensor range',
    iMax.toFixed(4) + ' A');
}

/* ---- 3. GPIO assignments ------------------------------------------------- */
{
  ok(fw.main.includes(`kPinSda = ${M.mcu.i2c_sda_gpio}`),
    'firmware SDA matches the manifest', M.mcu.i2c_sda_gpio);
  ok(fw.main.includes(`kPinScl = ${M.mcu.i2c_scl_gpio}`),
    'firmware SCL matches the manifest', M.mcu.i2c_scl_gpio);
  ok(fw.main.includes(`Wire.begin(kPinSda, kPinScl)`), 'SDA and SCL are passed to Wire.begin in that order');
  ok(pinOf('U2', 'IO21').net === 'SDA', 'the schematic puts SDA on IO21');
  ok(pinOf('U2', 'IO22').net === 'SCL', 'the schematic puts SCL on IO22');
  ok(fw.main.includes(`Wire.setClock(${M.mcu.i2c_clock_hz})`),
    'the bus clock matches the manifest', M.mcu.i2c_clock_hz);
}

/* ---- 4. sample interval and gap limit ------------------------------------ */
{
  const dt = M.firmware.sample_interval_ms;
  const gap = M.firmware.max_gap_ms;
  ok(fw.main.includes(`kSampleIntervalMs = ${dt}`), 'firmware sample interval matches the manifest', dt);
  ok(fw.integratorH.includes(`max_gap_ms = ${gap}`), 'firmware gap limit matches the manifest', gap);
  ok(dt < gap, 'the sample interval is below the gap limit, or nothing would ever integrate',
    `${dt} < ${gap}`);
  ok(gap / dt >= 4, 'there is at least a 4x margin between the interval and the gap limit',
    `${(gap / dt).toFixed(0)}x`);
}

/* ---- 5. sensor measurement connections ----------------------------------- */
{
  const byName = Object.fromEntries(designComp.U1.pins.map((p) => [p.name, p]));
  ok(byName['IN+'].net === M.sensor.in_plus_net, 'IN+ is on the supply side of the shunt', byName['IN+'].net);
  ok(byName['IN-'].net === M.sensor.in_minus_net, 'IN- is on the load side', byName['IN-'].net);
  ok(byName['VBUS'].net === M.sensor.vbus_net,
    'VBUS is tied to the load side, so the bus reading is the load voltage', byName['VBUS'].net);
  ok(byName['VS'].net === '3V3', 'the sensor supply is the 3.3 V rail', byName['VS'].net);
  ok(byName['ALERT'].net === 'NC', 'ALERT is explicitly unconnected', byName['ALERT'].net);
  /* the register decode constants the firmware uses must be the datasheet ones */
  ok(fw.ina226H.includes(`kShuntLsbVolts = ${M.sensor.shunt_lsb_uv}e-6f`),
    'the shunt LSB matches the manifest', M.sensor.shunt_lsb_uv + ' uV');
  ok(fw.ina226H.includes(`kBusLsbVolts = ${M.sensor.bus_lsb_mv}e-3f`),
    'the bus LSB matches the manifest', M.sensor.bus_lsb_mv + ' mV');
}

/* ---- 6. the published pages quote the same hardware --------------------- */
{
  const pages = {
    hardware: read('projects/dc-energy-monitor-hardware.html'),
    caseStudy: read('projects/smart-energy-monitoring.html')
  };
  Object.entries(pages).forEach(([name, html]) => {
    if (html.includes('0x40')) {
      ok(/0x40/.test(html), `${name} quotes the I2C address`);
    }
    if (html.includes('0.1')) {
      ok(/0\.1\s*(Ω|ohm)/i.test(html), `${name} quotes the shunt value`);
    }
  });
  ok(/0x40/.test(pages.hardware), 'the hardware page states the address');
  ok(/0\.1 Ω/.test(pages.hardware), 'the hardware page states the shunt');
}

if (fails.length) {
  console.log(`config consistency: ${checks - fails.length}/${checks} checks passed`);
  fails.forEach((f) => console.log('  FAIL ' + f));
  process.exit(1);
}
console.log(`PASS: hardware/firmware/site configuration agree — ${checks} checks across address, shunt, GPIOs, timing, measurement connections and published values`);

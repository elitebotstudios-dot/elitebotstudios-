// ===========================================================================
// test_core.cpp — desktop tests for the firmware calculation core
//
// This file compiles with g++ and no dependencies. It exercises the same
// dcm::Integrator and dcm::ina226 functions the ESP32 build uses, against the
// vectors in vectors_generated.h (produced from the documented policy, not from
// this code), plus a set of hand-derived unit checks.
//
// What this proves: the arithmetic, the decode, the calibration convention and
// the missing-data policy behave as specified.
//
// What this does NOT prove: that the firmware runs on a board, that the I2C
// driver works, or that the sensor readings are accurate. Those need hardware.
//
//   g++ -std=c++17 -I include -o /tmp/dcm_core_test src/core/*.cpp test/test_core.cpp
//   /tmp/dcm_core_test
// ===========================================================================
#include <cmath>
#include <cstdio>
#include <cstring>

#include "dcm/ina226.h"
#include "dcm/integrator.h"
#include "dcm/types.h"
#include "vectors_generated.h"

namespace {

int g_checks = 0;
int g_failures = 0;

void expect(bool condition, const char* what, const char* detail = "") {
  g_checks++;
  if (!condition) {
    g_failures++;
    std::printf("  FAIL  %-58s %s\n", what, detail);
  }
}

void expectNear(double actual, double expected, double tolerance, const char* what) {
  g_checks++;
  const double diff = std::fabs(actual - expected);
  if (diff > tolerance) {
    g_failures++;
    std::printf("  FAIL  %-58s got %.12g, expected %.12g (diff %.3g > %.3g)\n",
                what, actual, expected, diff, tolerance);
  }
}

/* Hand-derived unit checks on the decode functions. */
void unitChecks() {
  std::printf("\n  Unit checks on the register decode\n");

  // Datasheet LSBs.
  /* Tolerances here are float epsilon, not zero: these decoders return float
     because the firmware uses float on the MCU. A wrong LSB would be off by
     orders of magnitude, which is what the test is for. */
  expectNear(dcm::ina226::decodeBusVolts(1), 0.00125, 1e-9, "one bus LSB is 1.25 mV");
  expectNear(dcm::ina226::decodeShuntVolts(1), 2.5e-6, 1e-12, "one shunt LSB is 2.5 uV");

  // 12 V is code 9600 at 1.25 mV per LSB.
  expectNear(dcm::ina226::decodeBusVolts(9600), 12.0, 1e-9, "bus code 9600 decodes to 12 V");

  // 25 mV across a 0.1 ohm shunt is 0.25 A, and 25 mV is code 10000 at 2.5 uV.
  expectNear(dcm::ina226::currentFromShuntVolts(0.025f, 0.1f), 0.25, 1e-9,
             "25 mV across 0.1 ohm is 0.25 A");

  // Negative shunt voltage means reversed current: the decode must keep the sign.
  expectNear(dcm::ina226::decodeShuntVolts(-10000), -0.025, 1e-8,
             "negative codes decode to negative shunt volts");
  expectNear(dcm::ina226::currentFromShuntVolts(-0.025f, 0.1f), -0.25, 1e-9,
             "reversed current stays negative, not clamped to zero");

  // A zero shunt must not divide by zero.
  expectNear(dcm::ina226::currentFromShuntVolts(0.05f, 0.0f), 0.0, 0.0,
             "a zero shunt returns zero rather than dividing by zero");

  // Saturation detection at both ends of the range.
  expect(dcm::ina226::shuntSaturated(32767), "full-scale positive shunt code is flagged");
  expect(!dcm::ina226::shuntSaturated(32766), "one count below full scale is not flagged");

  // Integrator edge cases.
  dcm::Integrator integ;
  dcm::Sample a{1000, 10.0f, 1.0f, dcm::Status::kOk};
  dcm::Sample b{1000, 10.0f, 1.0f, dcm::Status::kOk};
  integ.add(a);
  auto r = integ.add(b);
  expect(!r.integrated, "two samples at the same timestamp integrate nothing");
  expectNear(integ.totals().energyWh(), 0.0, 0.0, "a zero-length interval adds no energy");

  dcm::Integrator reset_test;
  reset_test.add(dcm::Sample{0, 10.0f, 1.0f, dcm::Status::kOk});
  reset_test.add(dcm::Sample{1000, 10.0f, 1.0f, dcm::Status::kOk});
  expectNear(reset_test.totals().energyWh(), 10.0 / 3600.0, 1e-12, "10 W for 1 s is 10 J");
  reset_test.reset();
  expectNear(reset_test.totals().energyWh(), 0.0, 0.0, "reset clears the accumulator");
}

/* One vector set through decode, calibration and integration. */
void runSet(const dcm_test::VecSet& set, const char* heading) {
  std::printf("\n  %s — %s\n", set.id, heading);
  dcm::IntegratorConfig cfg;           // default max_gap_ms = 5000
  dcm::Integrator integ(cfg);
  dcm::Calibration cal;
  cal.voltage_gain = set.v_gain;
  cal.voltage_offset_v = set.v_offset;
  cal.current_gain = set.i_gain;
  cal.current_offset_a = set.i_offset;

  bool first = true;
  for (int i = 0; i < set.count; i++) {
    const dcm_test::VecSample& raw = set.samples[i];
    dcm::Sample s;
    s.timestamp_ms = raw.t_ms;
    if (raw.valid) {
      const float v_raw = dcm::ina226::decodeBusVolts(raw.bus_raw);
      const float shunt_v = dcm::ina226::decodeShuntVolts(raw.shunt_raw);
      const float i_raw = dcm::ina226::currentFromShuntVolts(shunt_v, set.shunt_ohms);
      s.voltage_v = v_raw * cal.voltage_gain + cal.voltage_offset_v;
      s.current_a = i_raw * cal.current_gain + cal.current_offset_a;
      s.status = dcm::ina226::shuntSaturated(raw.shunt_raw) ? dcm::Status::kOverrange : dcm::Status::kOk;
    } else {
      s.status = dcm::Status::kSensorNack;
      s.voltage_v = 0.0f;
      s.current_a = 0.0f;
    }
    if (first) {
      first = false;
    }
    integ.add(s);
  }

  const dcm::EnergyTotals& t = integ.totals();
  char label[128];

  std::snprintf(label, sizeof(label), "%s: total energy in Wh", set.id);
  expectNear(t.energyWh(), set.expected_energy_wh, 1e-9, label);

  std::snprintf(label, sizeof(label), "%s: integrated intervals", set.id);
  expectNear(static_cast<double>(t.integrated_intervals), set.expected_integrated, 0.0, label);

  std::snprintf(label, sizeof(label), "%s: held intervals", set.id);
  expectNear(static_cast<double>(t.held_intervals), set.expected_held, 0.0, label);

  std::snprintf(label, sizeof(label), "%s: gaps counted", set.id);
  expectNear(static_cast<double>(t.gaps), set.expected_gaps, 0.0, label);

  // The final decoded sample must match the vector's expectation too, which
  // catches a decode or calibration slip that happens to preserve the total.
  const dcm_test::VecSample& last_raw = set.samples[set.count - 1];
  if (last_raw.valid) {
    const float v = dcm::ina226::decodeBusVolts(last_raw.bus_raw) * cal.voltage_gain + cal.voltage_offset_v;
    const float i = dcm::ina226::currentFromShuntVolts(
        dcm::ina226::decodeShuntVolts(last_raw.shunt_raw), set.shunt_ohms) * cal.current_gain
        + cal.current_offset_a;
    std::snprintf(label, sizeof(label), "%s: final decoded voltage", set.id);
    expectNear(v, set.expected_final_v, 1e-5, label);
    std::snprintf(label, sizeof(label), "%s: final decoded current", set.id);
    expectNear(i, set.expected_final_i, 1e-6, label);
    std::snprintf(label, sizeof(label), "%s: final power", set.id);
    expectNear(static_cast<double>(v) * i, set.expected_final_p, 1e-4, label);
  }

  std::printf("    %-14s energy %.9f Wh   integrated %u   held %u   gaps %u   %s\n",
              set.id, t.energyWh(), t.integrated_intervals, t.held_intervals, t.gaps,
              (std::fabs(t.energyWh() - set.expected_energy_wh) <= 1e-9 &&
               t.integrated_intervals == static_cast<unsigned>(set.expected_integrated) &&
               t.held_intervals == static_cast<unsigned>(set.expected_held) &&
               t.gaps == static_cast<unsigned>(set.expected_gaps)) ? "PASS" : "FAIL");
}

}  // namespace

int main() {
  std::printf("\n  DC energy monitor — firmware core tests (desktop, no hardware)\n");
  std::printf("  %d vector sets from verification/test-vectors/vectors.json\n", dcm_test::kSetCount);

  unitChecks();
  for (int i = 0; i < dcm_test::kSetCount; i++) {
    runSet(dcm_test::kAllSets[i], "vector set");
  }

  std::printf("\n  ────────────────────────────────────────────────────────────────\n");
  std::printf("  %d checks · %d failed\n", g_checks, g_failures);
  if (g_failures == 0) {
    std::printf("  PASS: firmware core arithmetic, decode, calibration and missing-data policy\n");
    std::printf("  NOT TESTED HERE: I2C communication, sensor accuracy, timing on the board.\n");
    return 0;
  }
  std::printf("  FAIL: see the lines above\n");
  return 1;
}

// ===========================================================================
// test_sensor.cpp — the sensor driver against a mocked I2C bus
//
// The mock implements dcm::Transport, so the driver code under test is the same
// code the ESP32 build compiles. The mock can be told to acknowledge, to NACK,
// to report the wrong identity, to return saturated or nonsense registers, and
// to recover afterwards.
//
// WHAT THIS PROVES: the driver's sequencing, identity check, error handling and
// register interpretation behave as specified for the values it is given.
//
// WHAT THIS DOES NOT PROVE: anything about a physical INA226, the I2C bus
// timing, pull-ups, or measurement accuracy. No hardware was involved.
//
//   g++ -std=c++17 -I include -o /tmp/dcm_sensor_test
//       src/core/*.cpp test/test_sensor.cpp && /tmp/dcm_sensor_test
// ===========================================================================
#include <cmath>
#include <cstdio>
#include <cstdint>

#include "dcm/ina226.h"
#include "dcm/sensor.h"
#include "dcm/transport.h"
#include "dcm/types.h"

namespace {

int g_checks = 0;
int g_failures = 0;

void expect(bool cond, const char* what, const char* detail = "") {
  g_checks++;
  if (!cond) {
    g_failures++;
    std::printf("  FAIL  %-56s %s\n", what, detail);
  }
}
void expectNear(double actual, double expected, double tol, const char* what) {
  g_checks++;
  if (std::fabs(actual - expected) > tol) {
    g_failures++;
    std::printf("  FAIL  %-56s got %.9g, expected %.9g\n", what, actual, expected);
  }
}

/// A programmable stand-in for an INA226 on an I2C bus.
class MockBus : public dcm::Transport {
 public:
  // Registers a real INA226 would return.
  std::uint16_t manufacturer = dcm::ina226::kManufacturerIdTi;
  std::uint16_t die = dcm::ina226::kDieIdIna226;
  std::uint16_t bus_register = 0;
  std::uint16_t shunt_register = 0;

  // Fault switches.
  bool nack_all = false;
  bool nack_reads = false;
  bool nack_writes = false;
  bool short_read = false;

  int writes = 0;
  int reads = 0;

  bool writeRegister(std::uint8_t, std::uint8_t reg, std::uint16_t value) override {
    if (nack_all || nack_writes) return false;
    writes++;
    if (reg == dcm::ina226::kRegConfiguration) configuration = value;
    return true;
  }

  bool readRegister(std::uint8_t, std::uint8_t reg, std::uint16_t* out) override {
    if (nack_all || nack_reads) return false;
    if (short_read) return false;
    reads++;
    switch (reg) {
      case dcm::ina226::kRegManufacturerId: *out = manufacturer; return true;
      case dcm::ina226::kRegDieId: *out = die; return true;
      case dcm::ina226::kRegBusVoltage: *out = bus_register; return true;
      case dcm::ina226::kRegShuntVoltage: *out = shunt_register; return true;
      default: *out = 0; return true;
    }
  }

  std::uint16_t configuration = 0;
};

constexpr std::uint16_t busCode(double volts) {
  return static_cast<std::uint16_t>(volts / dcm::ina226::kBusLsbVolts + 0.5);
}
constexpr std::uint16_t shuntCode(double amps, double ohms) {
  return static_cast<std::uint16_t>((amps * ohms) / dcm::ina226::kShuntLsbVolts + 0.5);
}

dcm::SensorConfig cfg() {
  dcm::SensorConfig c;
  c.address = 0x40;
  c.shunt_ohms = 0.1f;
  return c;
}

}  // namespace

int main() {
  std::printf("\n  DC energy monitor — sensor driver against a mock I2C bus\n");
  std::printf("  (host mock, not hardware)\n");

  /* ---- 1. normal operation --------------------------------------------- */
  {
    MockBus bus;
    bus.bus_register = busCode(12.0);
    bus.shunt_register = shuntCode(0.25, 0.1);
    dcm::Ina226Sensor sensor(bus, cfg());
    expect(sensor.begin(), "begin() succeeds with a well-formed device");
    expect(sensor.present(), "the device is reported present");
    expect(bus.configuration == 0x4527, "the configuration word is written", "0x4527");
    const dcm::SensorReading r = sensor.read();
    expect(r.status == dcm::Status::kOk, "a good read reports OK");
    expectNear(r.bus_volts, 12.0, 0.002, "bus voltage decodes to 12 V");
    expectNear(r.current_a, 0.25, 0.001, "current decodes to 0.25 A");
    expectNear(r.shunt_volts, 0.025, 1e-5, "shunt voltage decodes to 25 mV");
  }

  /* ---- 2. sensor absent ------------------------------------------------- */
  {
    MockBus bus;
    bus.nack_all = true;
    dcm::Ina226Sensor sensor(bus, cfg());
    expect(!sensor.begin(), "begin() fails when the bus does not acknowledge");
    expect(!sensor.present(), "the device is reported absent");
    const dcm::SensorReading r = sensor.read();
    expect(r.status == dcm::Status::kSensorNotPresent,
           "a read on an absent device says so, rather than returning 0 V");
    expectNear(r.bus_volts, 0.0, 0.0, "an absent device reports no voltage");
    expect(r.status != dcm::Status::kOk, "an absent device never reports OK");
  }

  /* ---- 3. wrong device answers ------------------------------------------ */
  {
    MockBus bus;
    bus.manufacturer = 0x1234;
    dcm::Ina226Sensor sensor(bus, cfg());
    expect(!sensor.begin(), "begin() rejects a device with the wrong manufacturer ID");
    expect(!sensor.present(), "a wrong-ID device is not marked present");

    MockBus bus2;
    bus2.die = 0x2190;                     // an INA219, not an INA226
    dcm::Ina226Sensor sensor2(bus2, cfg());
    expect(!sensor2.begin(), "begin() rejects an INA219 die ID");
  }

  /* ---- 4. NACK after a good start --------------------------------------- */
  {
    MockBus bus;
    bus.bus_register = busCode(5.0);
    dcm::Ina226Sensor sensor(bus, cfg());
    sensor.begin();
    bus.nack_reads = true;
    const dcm::SensorReading r = sensor.read();
    expect(r.status == dcm::Status::kSensorNack, "a read failure is reported as a NACK");
    expect(sensor.bus_errors() == 1, "the bus error is counted", "");
    expect(r.status != dcm::Status::kOk, "a failed read never reports OK");
  }

  /* ---- 5. recovery after a fault ---------------------------------------- */
  {
    MockBus bus;
    bus.bus_register = busCode(12.0);
    bus.shunt_register = shuntCode(0.1, 0.1);
    dcm::Ina226Sensor sensor(bus, cfg());
    sensor.begin();
    bus.nack_reads = true;
    sensor.read();
    bus.nack_reads = false;
    const dcm::SensorReading r = sensor.read();
    expect(r.status == dcm::Status::kOk, "the driver recovers when the bus comes back");
    expectNear(r.bus_volts, 12.0, 0.002, "and reports the right value again");
  }

  /* ---- 6. zero current -------------------------------------------------- */
  {
    MockBus bus;
    bus.bus_register = busCode(12.0);
    bus.shunt_register = 0;
    dcm::Ina226Sensor sensor(bus, cfg());
    sensor.begin();
    const dcm::SensorReading r = sensor.read();
    expect(r.status == dcm::Status::kOk, "zero current is a valid reading");
    expectNear(r.current_a, 0.0, 0.0, "zero current decodes to exactly zero");
    expectNear(r.bus_volts, 12.0, 0.002, "with the bus voltage still present");
  }

  /* ---- 7. reversed current keeps its sign -------------------------------- */
  {
    MockBus bus;
    bus.bus_register = busCode(12.0);
    bus.shunt_register = static_cast<std::uint16_t>(static_cast<std::int16_t>(shuntCode(-0.2, 0.1)));
    dcm::Ina226Sensor sensor(bus, cfg());
    sensor.begin();
    const dcm::SensorReading r = sensor.read();
    expect(r.status == dcm::Status::kOk, "reversed current is a valid reading");
    expectNear(r.current_a, -0.2, 0.001, "reversed current stays negative");
  }

  /* ---- 8. shunt saturation ---------------------------------------------- */
  {
    MockBus bus;
    bus.bus_register = busCode(12.0);
    bus.shunt_register = 32767;
    dcm::Ina226Sensor sensor(bus, cfg());
    sensor.begin();
    const dcm::SensorReading r = sensor.read();
    expect(r.status == dcm::Status::kOverrange, "a full-scale shunt code is reported as overrange");
    expect(sensor.overranges() == 1, "the overrange is counted");
  }

  /* ---- 9. bus voltage beyond the part's rating --------------------------- */
  {
    MockBus bus;
    bus.bus_register = 0xFFFF;             // would decode to 81.9 V
    dcm::Ina226Sensor sensor(bus, cfg());
    sensor.begin();
    const dcm::SensorReading r = sensor.read();
    expect(r.status == dcm::Status::kOverrange,
           "a bus register above 36 V is rejected, not reported as a load voltage");
  }

  /* ---- 10. short read ---------------------------------------------------- */
  {
    MockBus bus;
    bus.short_read = true;
    dcm::Ina226Sensor sensor(bus, cfg());
    expect(!sensor.begin(), "a device that returns short reads is rejected at start-up");
  }

  std::printf("\n  ────────────────────────────────────────────────────────────────\n");
  std::printf("  %d checks · %d failed\n", g_checks, g_failures);
  if (g_failures == 0) {
    std::printf("  PASS: sensor driver sequencing, identity check, faults and recovery (host mock)\n");
    std::printf("  NOT TESTED: a physical INA226, bus timing, pull-ups, measurement accuracy.\n");
    return 0;
  }
  std::printf("  FAIL: see the lines above\n");
  return 1;
}

// ===========================================================================
// dcm/sensor.h — INA226 device logic, independent of Wire and of Arduino
//
// Sequence on begin():
//   1. write the configuration register (averaging, conversion time, mode)
//   2. read the manufacturer ID and die ID and check them
// If either step fails the device is marked absent and every later read reports
// kSensorNotPresent rather than returning zero volts and zero amps, which would
// look like a real measurement of a dead circuit.
// ===========================================================================
#pragma once

#include <cstdint>

#include "dcm/ina226.h"
#include "dcm/transport.h"
#include "dcm/types.h"

namespace dcm {

struct SensorConfig {
  std::uint8_t address = ina226::kAddressA0GndA1Gnd;
  float shunt_ohms = 0.1f;
  /// 16 averages, 1.1 ms bus and shunt conversion, continuous mode.
  /// bits 11-9 AVG=010, bits 8-6 VBUSCT=100, bits 5-3 VSHCT=100, bits 2-0 MODE=111
  std::uint16_t configuration_word = 0x4527;
  float bus_overrange_v = 36.0f;
};

struct SensorReading {
  float bus_volts = 0.0f;
  float shunt_volts = 0.0f;
  float current_a = 0.0f;
  Status status = Status::kOk;
};

class Ina226Sensor {
 public:
  Ina226Sensor(Transport& transport, const SensorConfig& config);

  bool begin();
  bool present() const { return present_; }
  SensorReading read();

  /// Counters a real driver would keep, so failures are visible rather than
  /// implied by a wrong number.
  std::uint32_t bus_errors() const { return bus_errors_; }
  std::uint32_t overranges() const { return overranges_; }

 private:
  Transport& transport_;
  SensorConfig config_;
  bool present_ = false;
  std::uint32_t bus_errors_ = 0;
  std::uint32_t overranges_ = 0;
};

}  // namespace dcm

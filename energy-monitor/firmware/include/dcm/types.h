// ===========================================================================
// dcm/types.h — shared types and units for the DC energy monitor firmware
//
// Every quantity carries its unit in the name. There are no bare "value"
// variables anywhere in this firmware: an unlabelled float in a measurement
// system is how unit errors survive to the bench.
//
// This header is platform-free. It is compiled on the ESP32 and, unchanged, on
// a desktop for the unit tests.
// ===========================================================================
#pragma once

#include <cstdint>

namespace dcm {

enum class Status : std::uint8_t {
  kOk = 0,
  kSensorNotPresent,   // I2C probe failed at start-up
  kSensorNack,         // the device did not acknowledge a read
  kInvalidReading,     // decoded values failed a sanity check
  kOverrange,          // bus voltage or shunt voltage at full scale
  kEnergyHeld,         // interval skipped on purpose; energy deliberately not advanced
};

const char* statusText(Status s);

// Corrections are applied in engineering units:  corrected = raw * gain + offset
struct Calibration {
  float voltage_gain = 1.0f;      // dimensionless
  float voltage_offset_v = 0.0f;  // V
  float current_gain = 1.0f;      // dimensionless
  float current_offset_a = 0.0f;  // A
};

struct Sample {
  std::uint32_t timestamp_ms = 0;  // milliseconds since boot; monotonic, wraps at 2^32
  float voltage_v = 0.0f;
  float current_a = 0.0f;
  Status status = Status::kOk;

  bool valid() const { return status == Status::kOk; }
};

struct EnergyTotals {
  double import_j = 0.0;   // energy delivered to the load
  double export_j = 0.0;   // energy returned (reversed current); tracked, not hidden
  std::uint32_t integrated_intervals = 0;
  std::uint32_t held_intervals = 0;     // skipped by the gap or invalid-sample policy
  std::uint32_t gaps = 0;               // intervals longer than the configured maximum
  double energyWh() const { return (import_j - export_j) / 3600.0; }
};

}  // namespace dcm

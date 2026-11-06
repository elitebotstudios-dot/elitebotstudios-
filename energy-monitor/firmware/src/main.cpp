// ===========================================================================
// main.cpp — ESP32 application layer for the DC energy monitor (DCM-HW-V1)
//
// This file is the only part of the firmware that touches hardware. It is built
// by PlatformIO for env:esp32dev and is NOT compiled on the desktop, where only
// the calculation core is built and tested.
//
// STATUS: compiled nowhere. No ESP32 toolchain was available in the authoring
// environment, so this file has been written and reviewed but never compiled,
// flashed or run. Treat the first build as a bring-up exercise, not a release.
//
// Wiring (DCM-HW-V1 rev A):
//   ESP32-DevKitC 3V3  -> J3 pin 1 -> INA226 module VCC
//   ESP32-DevKitC GND  -> J3 pin 2 -> module GND (common ground with the load)
//   ESP32 GPIO21       -> J3 pin 3 -> SDA (4k7 pull-up to 3V3 on the carrier)
//   ESP32 GPIO22       -> J3 pin 4 -> SCL (4k7 pull-up to 3V3 on the carrier)
//
// Serial output is CSV on the USB serial port at 115200 baud:
//   timestamp_ms,voltage_V,current_A,power_W,energy_Wh,status
//
// The timestamp is milliseconds since boot, not wall-clock time. This design
// has no real-time clock, so no date or time of day is claimed anywhere.
// ===========================================================================
#if defined(ARDUINO) || defined(ESP32) || defined(ESP_PLATFORM)

#include <Arduino.h>
#include <memory>
#include <Wire.h>

#include "dcm/ina226.h"
#include "dcm/integrator.h"
#include "dcm/sensor.h"
#include "dcm/transport.h"
#include "dcm/types.h"

namespace {

constexpr std::uint8_t kSensorAddress = dcm::ina226::kAddressA0GndA1Gnd;  // 0x40
constexpr std::uint8_t kPinSda = 21;
constexpr std::uint8_t kPinScl = 22;
constexpr std::uint32_t kSampleIntervalMs = 250;   // four samples per second
constexpr float kShuntOhms = 0.1f;                 // R1 on the carrier

// INA226 configuration word: 16 averages, 1.1 ms bus and shunt conversion
// time, continuous mode. Written as a literal because the bit fields are easy
// to misread; the comment names each field so it can be checked against the
// datasheet rather than trusted.
//   bit 15    reset = 0
//   bits 11-9 AVG = 010 (16 samples)
//   bits 8-6  VBUSCT = 100 (1.1 ms)
//   bits 5-3  VSHCT = 100 (1.1 ms)
//   bits 2-0  MODE = 111 (shunt and bus, continuous)
constexpr std::uint16_t kConfigWord = 0x4527;

dcm::Calibration g_calibration;      // identity until calibrated
dcm::IntegratorConfig g_integrator_config;          // default 5 s gap limit
dcm::Integrator g_integrator{dcm::IntegratorConfig{}};
std::uint32_t g_next_sample_ms = 0;
std::unique_ptr<dcm::Ina226Sensor> g_sensor;

// The I2C boundary, implemented with Wire. Everything above this line is the
// same dcm::Ina226Sensor the host tests exercise through a mock bus.
class WireTransport : public dcm::Transport {
 public:
  bool writeRegister(std::uint8_t address, std::uint8_t reg, std::uint16_t value) override {
    Wire.beginTransmission(address);
    Wire.write(reg);
    Wire.write(static_cast<std::uint8_t>(value >> 8));
    Wire.write(static_cast<std::uint8_t>(value & 0xFF));
    return Wire.endTransmission() == 0;
  }

  bool readRegister(std::uint8_t address, std::uint8_t reg, std::uint16_t* out) override {
    Wire.beginTransmission(address);
    Wire.write(reg);
    if (Wire.endTransmission(false) != 0) return false;
    if (Wire.requestFrom(address, static_cast<std::uint8_t>(2)) != 2) return false;
    const std::uint8_t hi = Wire.read();
    const std::uint8_t lo = Wire.read();
    *out = static_cast<std::uint16_t>((hi << 8) | lo);
    return true;
  }
};

WireTransport g_transport;
dcm::SensorConfig g_sensor_config;

}  // namespace

// setup() and loop() must have external linkage: the Arduino core looks for them
// by name from outside this translation unit.
void setup() {
  Serial.begin(115200);
  Wire.begin(kPinSda, kPinScl);
  Wire.setClock(100000);            // 100 kHz: conservative for the first bring-up

  delay(50);                        // let the sensor supply settle after power-up
  g_sensor_config.address = kSensorAddress;
  g_sensor_config.shunt_ohms = kShuntOhms;
  g_sensor_config.configuration_word = kConfigWord;
  g_sensor.reset(new dcm::Ina226Sensor(g_transport, g_sensor_config));
  const bool sensor_present = g_sensor->begin();

  Serial.println();
  Serial.println("# Elite Bot Studios — DC Energy Monitor, firmware v1");
  Serial.println("# hardware: DCM-HW-V1 rev A (INA226, 0.1 ohm shunt, 3.3 V logic)");
  Serial.println("# timestamp is milliseconds since boot; there is no RTC in this design");
  if (!sensor_present) {
    Serial.println("# STATUS: no INA226 at 0x40. Check 3V3, GND, SDA, SCL, the A0/A1 straps,");
    Serial.println("#         and whether the bus acknowledges at all.");
  }
  // A sampling interval longer than the gap limit means no interval is ever
  // integrated: the accumulator would sit at zero while looking healthy.
  if (kSampleIntervalMs >= g_integrator_config.max_gap_ms) {
    Serial.println("# STATUS: sample interval is at or above the gap limit; no interval would integrate");
  }
  Serial.println("timestamp_ms,voltage_V,current_A,power_W,energy_Wh,status");
  g_next_sample_ms = millis();
}

void loop() {
  const std::uint32_t now = millis();
  if (static_cast<std::int32_t>(now - g_next_sample_ms) < 0) return;   // wrap-safe scheduling
  g_next_sample_ms += kSampleIntervalMs;

  dcm::Sample sample;
  sample.timestamp_ms = now;

  if (!g_sensor) {
    sample.status = dcm::Status::kSensorNotPresent;
  } else {
    const dcm::SensorReading reading = g_sensor->read();
    sample.status = reading.status;
    sample.voltage_v = reading.bus_volts * g_calibration.voltage_gain + g_calibration.voltage_offset_v;
    sample.current_a = reading.current_a * g_calibration.current_gain
                       + g_calibration.current_offset_a;
  }

  const dcm::IntegrationResult r = g_integrator.add(sample);
  const dcm::EnergyTotals& totals = g_integrator.totals();

  Serial.print(sample.timestamp_ms);
  Serial.print(',');
  Serial.print(sample.voltage_v, 4);
  Serial.print(',');
  Serial.print(sample.current_a, 5);
  Serial.print(',');
  Serial.print(sample.voltage_v * sample.current_a, 4);
  Serial.print(',');
  Serial.print(totals.energyWh(), 6);
  Serial.print(',');
  Serial.println(dcm::statusText(sample.status));

  // A held interval is reported once, so a silent gap in the data cannot look
  // like a period of zero power.
  if (!r.integrated && sample.status == dcm::Status::kOk) {
    Serial.print("# interval not integrated (gap or held): dt_ms=");
    Serial.println(r.interval_ms, 0);
  }
}

#endif  // ARDUINO / ESP32

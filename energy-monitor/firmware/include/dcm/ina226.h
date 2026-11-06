// ===========================================================================
// dcm/ina226.h — INA226 register decoding, independent of any I2C driver
//
// The decode functions take raw 16-bit register contents and return engineering
// units. Keeping them free of I2C makes them testable on a desktop with values
// derived from the datasheet, which is exactly what test/test_core.cpp does.
//
// Datasheet figures used here (Texas Instruments INA226 — verify against the
// current revision before relying on them):
//   shunt voltage LSB   2.5 µV, signed, ±81.92 mV full scale
//   bus voltage LSB     1.25 mV, unsigned, 0–36 V
//   supply              2.7–5.5 V
//   I2C addresses       0x40–0x4F selected by A0/A1
// ===========================================================================
#pragma once

#include <cstdint>

namespace dcm {
namespace ina226 {

constexpr float kShuntLsbVolts = 2.5e-6f;
constexpr float kBusLsbVolts = 1.25e-3f;
constexpr float kShuntFullScaleV = 0.08192f;
constexpr float kBusFullScaleV = 36.0f;

constexpr std::uint8_t kRegConfiguration = 0x00;
constexpr std::uint8_t kRegShuntVoltage = 0x01;
constexpr std::uint8_t kRegBusVoltage = 0x02;
constexpr std::uint8_t kRegPower = 0x03;
constexpr std::uint8_t kRegCurrent = 0x04;
constexpr std::uint8_t kRegCalibration = 0x05;
constexpr std::uint8_t kRegMaskEnable = 0x06;
constexpr std::uint8_t kRegAlertLimit = 0x07;
constexpr std::uint8_t kRegManufacturerId = 0xFE;
constexpr std::uint8_t kRegDieId = 0xFF;

constexpr std::uint16_t kManufacturerIdTi = 0x5449;  // 'TI'
constexpr std::uint16_t kDieIdIna226 = 0x2260;
constexpr std::uint8_t kAddressA0GndA1Gnd = 0x40;

/// Shunt voltage register (signed 16-bit) to volts.
float decodeShuntVolts(std::int16_t raw);

/// Bus voltage register (unsigned 16-bit) to volts.
float decodeBusVolts(std::uint16_t raw);

/// Current from the shunt voltage and the known shunt resistance.
/// The firmware derives current from the shunt drop rather than from the
/// device's current register, so the result does not depend on the calibration
/// register having been written correctly.
float currentFromShuntVolts(float shunt_volts, float shunt_ohms);

/// True when the raw code sits at the end of the shunt range.
bool shuntSaturated(std::int16_t raw);

}  // namespace ina226
}  // namespace dcm

#include "dcm/sensor.h"

namespace dcm {

Ina226Sensor::Ina226Sensor(Transport& transport, const SensorConfig& config)
    : transport_(transport), config_(config) {}

bool Ina226Sensor::begin() {
  present_ = false;

  if (!transport_.writeRegister(config_.address, ina226::kRegConfiguration,
                               config_.configuration_word)) {
    bus_errors_++;
    return false;
  }

  std::uint16_t manufacturer = 0, die = 0;
  if (!transport_.readRegister(config_.address, ina226::kRegManufacturerId, &manufacturer) ||
      !transport_.readRegister(config_.address, ina226::kRegDieId, &die)) {
    bus_errors_++;
    return false;
  }

  if (manufacturer != ina226::kManufacturerIdTi || (die & 0xFFF0) != ina226::kDieIdIna226) {
    return false;   // something answered, but it is not an INA226
  }

  present_ = true;
  return true;
}

SensorReading Ina226Sensor::read() {
  SensorReading out;
  if (!present_) {
    out.status = Status::kSensorNotPresent;
    return out;
  }

  std::uint16_t bus_raw = 0, shunt_raw = 0;
  if (!transport_.readRegister(config_.address, ina226::kRegBusVoltage, &bus_raw) ||
      !transport_.readRegister(config_.address, ina226::kRegShuntVoltage, &shunt_raw)) {
    bus_errors_++;
    out.status = Status::kSensorNack;
    return out;
  }

  const auto shunt_signed = static_cast<std::int16_t>(shunt_raw);
  out.bus_volts = ina226::decodeBusVolts(bus_raw);
  out.shunt_volts = ina226::decodeShuntVolts(shunt_signed);
  out.current_a = ina226::currentFromShuntVolts(out.shunt_volts, config_.shunt_ohms);

  if (ina226::shuntSaturated(shunt_signed)) {
    overranges_++;
    out.status = Status::kOverrange;
    return out;
  }
  // The bus register is 15 bits plus a zero sign bit; a reading above the part's
  // rated 36 V means the input is being abused, not that the load is at 60 V.
  if (out.bus_volts > config_.bus_overrange_v) {
    overranges_++;
    out.status = Status::kOverrange;
    return out;
  }

  out.status = Status::kOk;
  return out;
}

}  // namespace dcm

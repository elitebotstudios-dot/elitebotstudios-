#include "dcm/ina226.h"

namespace dcm {
namespace ina226 {

float decodeShuntVolts(std::int16_t raw) {
  return static_cast<float>(raw) * kShuntLsbVolts;
}

float decodeBusVolts(std::uint16_t raw) {
  return static_cast<float>(raw) * kBusLsbVolts;
}

float currentFromShuntVolts(float shunt_volts, float shunt_ohms) {
  if (!(shunt_ohms > 0.0f)) return 0.0f;   // a zero shunt is a configuration error
  return shunt_volts / shunt_ohms;
}

bool shuntSaturated(std::int16_t raw) {
  return raw >= 32767 || raw <= -32768;
}

}  // namespace ina226
}  // namespace dcm

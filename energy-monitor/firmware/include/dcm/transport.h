// ===========================================================================
// dcm/transport.h — the I2C boundary, as an interface
//
// The sensor logic must be testable without an ESP32 and without a sensor. All
// it needs from the outside world is "write this register" and "read this
// register", so that is the whole interface. On the device it is implemented
// with Wire; in the host tests it is implemented by a mock that can NACK, return
// nonsense, or recover on demand.
//
// A host mock is not a sensor. Passing these tests says the logic handles the
// register values it is given; it says nothing about a physical device.
// ===========================================================================
#pragma once

#include <cstdint>

namespace dcm {

class Transport {
 public:
  virtual ~Transport() = default;

  /// Returns false on a bus error or a missing acknowledge.
  virtual bool writeRegister(std::uint8_t address, std::uint8_t reg, std::uint16_t value) = 0;

  /// Returns false on a bus error, a missing acknowledge, or a short read.
  virtual bool readRegister(std::uint8_t address, std::uint8_t reg, std::uint16_t* out) = 0;
};

}  // namespace dcm

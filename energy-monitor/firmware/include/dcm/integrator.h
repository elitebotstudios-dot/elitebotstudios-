// ===========================================================================
// dcm/integrator.h — energy accumulation with an explicit missing-data policy
//
// Rules, in order:
//   1. The interval used is (now - previous), from a 32-bit millisecond counter.
//      Unsigned subtraction is wrap-safe, so a rollover after 49.7 days gives a
//      correct delta instead of a negative one.
//   2. If either sample is invalid, the interval is NOT integrated: the
//      accumulator is held, the event is counted, and the previous sample is
//      replaced so the next interval does not span the missing data.
//   3. If the interval exceeds max_gap_ms it is treated as missing data: not
//      integrated, counted as a gap. Energy is never invented across a period
//      in which nothing was measured.
//   4. Otherwise the trapezoidal rule is applied to measured power.
// ===========================================================================
#pragma once

#include <cstdint>

#include "dcm/types.h"

namespace dcm {

struct IntegratorConfig {
  std::uint32_t max_gap_ms = 5000;
};

struct IntegrationResult {
  bool integrated = false;
  bool gap = false;
  double interval_ms = 0.0;
  double energy_wh = 0.0;
};

class Integrator {
 public:
  explicit Integrator(const IntegratorConfig& config = IntegratorConfig());

  IntegrationResult add(const Sample& sample);

  const EnergyTotals& totals() const { return totals_; }
  void reset();

 private:
  IntegratorConfig config_;
  EnergyTotals totals_;
  bool have_previous_ = false;
  Sample previous_{};
};

}  // namespace dcm

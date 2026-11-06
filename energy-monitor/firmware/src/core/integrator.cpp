#include "dcm/integrator.h"

#include <cmath>

namespace dcm {

const char* statusText(Status s) {
  switch (s) {
    case Status::kOk: return "OK";
    case Status::kSensorNotPresent: return "SENSOR_NOT_PRESENT";
    case Status::kSensorNack: return "SENSOR_NACK";
    case Status::kInvalidReading: return "INVALID_READING";
    case Status::kOverrange: return "OVERRANGE";
    case Status::kEnergyHeld: return "ENERGY_HELD";
  }
  return "UNKNOWN";
}

Integrator::Integrator(const IntegratorConfig& config) : config_(config) {}

void Integrator::reset() {
  totals_ = EnergyTotals{};
  have_previous_ = false;
  previous_ = Sample{};
}

IntegrationResult Integrator::add(const Sample& sample) {
  IntegrationResult result;
  result.energy_wh = totals_.energyWh();

  if (!have_previous_) {
    previous_ = sample;
    have_previous_ = true;
    return result;
  }

  // Wrap-safe: unsigned arithmetic gives the true elapsed time across rollover.
  const std::uint32_t dt_ms = sample.timestamp_ms - previous_.timestamp_ms;

  if (dt_ms == 0) {
    totals_.held_intervals++;
    previous_ = sample;
    return result;
  }

  if (!sample.valid() || !previous_.valid()) {
    totals_.held_intervals++;
    previous_ = sample;
    result.interval_ms = static_cast<double>(dt_ms);
    return result;
  }

  if (dt_ms > config_.max_gap_ms) {
    totals_.held_intervals++;
    totals_.gaps++;
    previous_ = sample;
    result.gap = true;
    result.interval_ms = static_cast<double>(dt_ms);
    return result;
  }

  const double dt_s = static_cast<double>(dt_ms) / 1000.0;
  const double p_prev = static_cast<double>(previous_.voltage_v) * previous_.current_a;
  const double p_now = static_cast<double>(sample.voltage_v) * sample.current_a;
  const double interval_j = 0.5 * (p_prev + p_now) * dt_s;

  if (interval_j >= 0.0) {
    totals_.import_j += interval_j;
  } else {
    totals_.export_j -= interval_j;
  }

  totals_.integrated_intervals++;
  previous_ = sample;
  result.integrated = true;
  result.interval_ms = static_cast<double>(dt_ms);
  result.energy_wh = totals_.energyWh();
  return result;
}

}  // namespace dcm

/**
 * Utilities for Workload Cockpit: Schmitt Hysteresis, dynamic retention rates, and lookahead display.
 */

export type WorkloadMode = "free" | "busy" | "hysteresis_hold";
export type HysteresisBand = "free" | "deadband" | "busy";

export const FREE_THRESHOLD = 0.55;
export const BUSY_THRESHOLD = 0.70;

/**
 * Schmitt Trigger Logic:
 * - score <= 0.55 -> free
 * - score > 0.70  -> busy
 * - 0.55 < score <= 0.70 -> Retain previousMode (default "free")
 */
export function resolveCockpitMode(
  score: number,
  previousMode: WorkloadMode = "free"
): WorkloadMode {
  if (score <= FREE_THRESHOLD) {
    return "free";
  }
  if (score > BUSY_THRESHOLD) {
    return "busy";
  }
  return previousMode === "busy" ? "busy" : "free";
}

/**
 * Returns which Schmitt Hysteresis threshold band a raw score falls into.
 */
export function getHysteresisBand(score: number): HysteresisBand {
  if (score <= FREE_THRESHOLD) {
    return "free";
  }
  if (score > BUSY_THRESHOLD) {
    return "busy";
  }
  return "deadband";
}

/**
 * Dynamic Retention Target scaled by active workload mode:
 * - Free Mode: 90% default target (in-depth retention)
 * - Busy Mode: 80% compressed target (preventing cognitive fatigue)
 */
export function getRetentionTarget(mode: WorkloadMode): number {
  return mode === "busy" ? 80 : 90;
}

/**
 * Formats lookahead days for header display.
 */
export function formatLookaheadDays(days: number): string {
  return `Continuous ${days}-Day Lookahead`;
}

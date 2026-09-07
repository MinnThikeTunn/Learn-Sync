import { describe, it, expect } from "vitest";
import { 
  resolveCockpitMode, 
  getRetentionTarget, 
  getHysteresisBand, 
  formatLookaheadDays 
} from "./workloadCockpitUtils";

describe("workloadCockpitUtils", () => {
  it("resolves Free Mode cutoff <= 55%", () => {
    expect(resolveCockpitMode(0.40, "free")).toBe("free");
    expect(resolveCockpitMode(0.55, "busy")).toBe("free");
    expect(getHysteresisBand(0.40)).toBe("free");
  });

  it("retains previous mode in dead-band 55% - 70%", () => {
    expect(resolveCockpitMode(0.65, "free")).toBe("free");
    expect(resolveCockpitMode(0.65, "busy")).toBe("busy");
    expect(getHysteresisBand(0.65)).toBe("deadband");
  });

  it("spikes into Busy Mode > 70%", () => {
    expect(resolveCockpitMode(0.72, "free")).toBe("busy");
    expect(resolveCockpitMode(0.95, "busy")).toBe("busy");
    expect(getHysteresisBand(0.85)).toBe("busy");
  });

  it("computes dynamic retention target based on mode", () => {
    expect(getRetentionTarget("free")).toBe(90);
    expect(getRetentionTarget("busy")).toBe(80);
    expect(getRetentionTarget("hysteresis_hold")).toBe(90);
  });

  it("formats lookahead horizon label accurately", () => {
    expect(formatLookaheadDays(1)).toBe("Continuous 1-Day Lookahead");
    expect(formatLookaheadDays(3)).toBe("Continuous 3-Day Lookahead");
    expect(formatLookaheadDays(7)).toBe("Continuous 7-Day Lookahead");
  });
});

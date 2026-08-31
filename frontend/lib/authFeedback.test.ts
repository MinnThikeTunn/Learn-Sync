import { describe, test, expect } from "vitest";
import { getAuthStageDetails } from "./authFeedback";

describe("getAuthStageDetails TDD Seam", () => {
  test("signup in email_sent stage requires user inbox check with email address", () => {
    const details = getAuthStageDetails("signup", "email_sent", {
      email: "alex@university.edu",
    });

    expect(details.isInboxNotice).toBe(true);
    expect(details.title).toContain("verification message");
    expect(details.description).toContain("alex@university.edu");
    expect(details.inboxTips).toBeDefined();
    expect(details.inboxTips.length).toBeGreaterThan(0);
    expect(details.inboxTips.some((tip) => tip.toLowerCase().includes("spam"))).toBe(true);
  });

  test("signin in processing stage shows loading indicator and stage badge", () => {
    const details = getAuthStageDetails("signin", "processing");

    expect(details.isSpinning).toBe(true);
    expect(details.badge).toContain("Authenticating");
    expect(details.isInboxNotice).toBe(false);
  });

  test("forgot in email_sent stage displays password reset inbox notice", () => {
    const details = getAuthStageDetails("forgot", "email_sent", {
      email: "student@learnsync.ai",
    });

    expect(details.isInboxNotice).toBe(true);
    expect(details.title).toContain("Reset Link Sent");
    expect(details.description).toContain("student@learnsync.ai");
  });

  test("signup in redirecting stage notifies immediate cockpit transfer", () => {
    const details = getAuthStageDetails("signup", "redirecting");

    expect(details.isSpinning).toBe(true);
    expect(details.title).toContain("Redirecting");
  });
});

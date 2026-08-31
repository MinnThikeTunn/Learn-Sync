export type AuthMode = "signin" | "signup" | "forgot";

export type AuthStage =
  | "idle"
  | "validating"
  | "processing"
  | "email_sent"
  | "redirecting"
  | "error";

export interface AuthStageDetails {
  title: string;
  description: string;
  badge: string;
  isSpinning: boolean;
  isInboxNotice: boolean;
  inboxTips: string[];
}

export function getAuthStageDetails(
  mode: AuthMode,
  stage: AuthStage,
  extraData?: { email?: string; errorMsg?: string }
): AuthStageDetails {
  const email = extraData?.email || "your email address";

  if (stage === "validating") {
    return {
      title: "Validating inputs...",
      description: "Checking form credentials and password requirements.",
      badge: "Step 1 of 3",
      isSpinning: true,
      isInboxNotice: false,
      inboxTips: [],
    };
  }

  if (stage === "processing") {
    if (mode === "signin") {
      return {
        title: "Authenticating account...",
        description: "Connecting to secure Supabase authentication...",
        badge: "Authenticating",
        isSpinning: true,
        isInboxNotice: false,
        inboxTips: [],
      };
    }
    if (mode === "signup") {
      return {
        title: "Creating student profile...",
        description: "Setting up your cognitive learning workspace...",
        badge: "Creating Profile",
        isSpinning: true,
        isInboxNotice: false,
        inboxTips: [],
      };
    }
    return {
      title: "Processing request...",
      description: "Preparing password reset dispatch...",
      badge: "Sending Request",
      isSpinning: true,
      isInboxNotice: false,
      inboxTips: [],
    };
  }

  if (stage === "email_sent") {
    if (mode === "forgot") {
      return {
        title: "Reset Link Sent! Check Your Inbox",
        description: `We sent password reset instructions to ${email}.`,
        badge: "Check Email",
        isSpinning: false,
        isInboxNotice: true,
        inboxTips: [
          `Open inbox for ${email}`,
          "Check spam or junk folder if not seen in 2 mins",
          "Click link inside email to reset your password",
        ],
      };
    }
    return {
      title: "We sent you the verification message",
      description: `We sent you the verification message to ${email}. Please check it.`,
      badge: "Inbox Action Required",
      isSpinning: false,
      isInboxNotice: true,
      inboxTips: [
        `Check inbox for ${email}`,
        "Check spam or junk folder if missing",
        "Click confirmation link to activate your student account",
      ],
    };
  }

  if (stage === "redirecting") {
    return {
      title: "Success! Redirecting to Cockpit...",
      description: "Preparing your context-aware adaptive learning cockpit.",
      badge: "Redirecting",
      isSpinning: true,
      isInboxNotice: false,
      inboxTips: [],
    };
  }

  return {
    title: "",
    description: "",
    badge: "",
    isSpinning: false,
    isInboxNotice: false,
    inboxTips: [],
  };
}

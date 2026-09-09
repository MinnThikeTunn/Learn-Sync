import { describe, test, expect, beforeAll } from "vitest";
import { loadEnvConfig } from "@next/env";

const env = loadEnvConfig(process.cwd());
Object.assign(process.env, env.combinedEnv);

describe("Supabase Auth Client Configuration & Sign In", () => {
  test("supabase client must be configured with a valid Supabase URL, not the dummy fallback", async () => {
    const { createClient } = await import("./supabase/client");
    const supabase = createClient();
    const supabaseUrl = (supabase as any).supabaseUrl;

    // Must have a real URL, not the dummy example.supabase.co fallback
    expect(supabaseUrl).toBeDefined();
    expect(supabaseUrl).not.toContain("example.supabase.co");
  });

  test("signInWithPassword should connect to real endpoint and not fail due to unresolvable example.supabase.co", async () => {
    const { createClient } = await import("./supabase/client");
    const supabase = createClient();
    const res = await supabase.auth.signInWithPassword({
      email: "test@example.com",
      password: "password123",
    });

    expect(res.error).toBeDefined();
    expect(res.error?.message).not.toMatch(/Failed to fetch|fetch failed|ENOTFOUND/i);
    // Real Supabase server responds with standard AuthApiError
    expect(res.error?.message).toBe("Invalid login credentials");
  });
});

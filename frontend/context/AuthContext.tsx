"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import type { User, Session } from "@supabase/supabase-js";
import { createClient } from "../lib/supabase/client";

export interface StudentProfile {
  id: string;
  email: string;
  full_name: string | null;
  learning_style: "visual" | "auditory" | "read_write" | "kinesthetic";
  secondary_learning_style?: "visual" | "auditory" | "read_write" | "kinesthetic" | null;
  assessment_scores?: Record<string, number>;
  target_retention: number;
  onboarding_completed: boolean;
  created_at?: string;
  updated_at?: string;
}

interface AuthContextType {
  user: User | null;
  session: Session | null;
  profile: StudentProfile | null;
  isLoading: boolean;
  signInWithPassword: (email: string, password: string) => Promise<{ error: Error | null }>;
  signUpWithPassword: (email: string, password: string, fullName?: string) => Promise<{ data?: any; error: Error | null }>;
  resetPassword: (email: string) => Promise<{ error: Error | null }>;
  updatePassword: (newPassword: string) => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  updateProfile: (updates: Partial<StudentProfile>) => Promise<{ error: Error | null }>;
  setLearningStyle: (style: StudentProfile["learning_style"]) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const supabase = createClient();

  const fetchProfile = useCallback(async (userId: string, userEmail?: string) => {
    try {
      const { data, error } = await supabase
        .from("profiles")
        .select("*")
        .eq("id", userId)
        .single();

      if (data) {
        setProfile(data as StudentProfile);
        if (typeof window !== "undefined" && data.learning_style) {
          localStorage.setItem("learnsync_learning_style", data.learning_style);
          localStorage.setItem("learnsync_onboarding_completed", String(data.onboarding_completed ?? false));
        }
      } else {
        // Automatically provision profile in Supabase if not created by trigger yet
        const defaultProf: StudentProfile = {
          id: userId,
          email: userEmail || "",
          full_name: userEmail ? userEmail.split("@")[0] : "Student",
          learning_style: "read_write",
          target_retention: 0.90,
          onboarding_completed: false,
        };

        // Attempt upsert so row exists in Supabase
        await supabase.from("profiles").upsert({
          id: userId,
          email: userEmail || "",
          full_name: defaultProf.full_name,
          learning_style: "read_write",
          target_retention: 0.90,
          onboarding_completed: false,
          updated_at: new Date().toISOString(),
        });

        setProfile(defaultProf);
      }
    } catch (err) {
      console.error("Error loading student profile:", err);
    }
  }, [supabase]);

  useEffect(() => {
    // 1. Initial Session Check
    const getInitialSession = async () => {
      try {
        const { data: { session: initialSession } } = await supabase.auth.getSession();
        setSession(initialSession);
        setUser(initialSession?.user ?? null);

        if (initialSession?.user) {
          await fetchProfile(initialSession.user.id, initialSession.user.email);
        }
      } catch (e) {
        console.error("Initial auth session check failed:", e);
      } finally {
        setIsLoading(false);
      }
    };

    getInitialSession();

    // 2. Realtime Auth State Listener
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, currentSession) => {
        setSession(currentSession);
        setUser(currentSession?.user ?? null);

        if (currentSession?.user) {
          await fetchProfile(currentSession.user.id, currentSession.user.email);
        } else {
          setProfile(null);
        }
        setIsLoading(false);
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [supabase, fetchProfile]);

  const signInWithPassword = async (email: string, password: string) => {
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      return { error };
    } catch (err: any) {
      return { error: err };
    }
  };

  const signUpWithPassword = async (email: string, password: string, fullName?: string) => {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
          },
        },
      });
      return { data, error };
    } catch (err: any) {
      return { data: null, error: err };
    }
  };


  const resetPassword = async (email: string) => {
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: typeof window !== "undefined" ? `${window.location.origin}/reset-password` : undefined,
      });
      return { error };
    } catch (err: any) {
      return { error: err };
    }
  };

  const updatePassword = async (newPassword: string) => {
    try {
      const { error } = await supabase.auth.updateUser({
        password: newPassword,
      });
      return { error };
    } catch (err: any) {
      return { error: err };
    }
  };

  const signOut = async () => {
    await supabase.auth.signOut();
    setUser(null);
    setSession(null);
    setProfile(null);
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  };

  const refreshProfile = async () => {
    if (user) {
      await fetchProfile(user.id, user.email);
    }
  };

  const updateProfile = async (updates: Partial<StudentProfile>) => {
    // 1. Optimistic Local State & Cache Update
    setProfile((prev) => {
      if (prev) return { ...prev, ...updates };
      return {
        id: user?.id || "guest",
        email: user?.email || "",
        full_name: "Student",
        learning_style: updates.learning_style || "visual",
        target_retention: 0.90,
        onboarding_completed: updates.onboarding_completed ?? false,
        ...updates,
      };
    });

    if (typeof window !== "undefined") {
      if (updates.learning_style) {
        localStorage.setItem("learnsync_learning_style", updates.learning_style);
      }
      if (updates.onboarding_completed !== undefined) {
        localStorage.setItem("learnsync_onboarding_completed", String(updates.onboarding_completed));
      }
    }

    // 2. Persist to Supabase if authenticated
    if (user) {
      try {
        const payload: Record<string, any> = {
          id: user.id,
          email: user.email,
          ...updates,
          updated_at: new Date().toISOString(),
        };

        const { error } = await supabase
          .from("profiles")
          .upsert(payload, { onConflict: "id" });

        if (error) {
          console.warn("Supabase profile upsert returned warning/error:", error.message);
        }
        return { error };
      } catch (err: any) {
        console.error("Supabase profile upsert exception:", err);
        return { error: err };
      }
    }

    return { error: null };
  };

  const setLearningStyle = async (style: StudentProfile["learning_style"]) => {
    await updateProfile({ learning_style: style });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        profile,
        isLoading,
        signInWithPassword,
        signUpWithPassword,
        resetPassword,
        updatePassword,
        signOut,
        refreshProfile,
        updateProfile,
        setLearningStyle,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

"use client";

import React, { useState } from "react";
import { X, Calendar, Plus, Clock, Tag, Award } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

interface ManualEventModalProps {
  isOpen: boolean;
  onClose: () => void;
  onEventCreated: () => void;
  userId?: string;
}

export default function ManualEventModal({
  isOpen,
  onClose,
  onEventCreated,
  userId,
}: ManualEventModalProps) {
  const [title, setTitle] = useState("");
  const [eventType, setEventType] = useState<"exam" | "assignment" | "quiz" | "project">("assignment");
  const [dueDate, setDueDate] = useState("");
  const [weight, setWeight] = useState("1.5");
  const [courseCode, setCourseCode] = useState("CS101");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !dueDate) {
      setError("Please specify event title and due date.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const effectiveUserId = userId || "00000000-0000-0000-0000-000000000001";
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        "X-Test-User-Id": effectiveUserId,
      };

      const payload = {
        title: title.trim(),
        event_type: eventType,
        start_time: new Date(dueDate).toISOString(),
        weight: parseFloat(weight) || 1.0,
        source: "manual",
      };

      const res = await fetch(`${API_URL}/events`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const supabase = createClient();
        const { error: insertError } = await supabase.from("events").insert({
          user_id: effectiveUserId,
          ...payload,
        });
        if (insertError) throw insertError;
      }

      setTitle("");
      setDueDate("");
      onEventCreated();
      onClose();
    } catch (err: any) {
      console.error("Error creating event:", err);
      setError(err?.message || "Failed to create event.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-[32px] border border-brand-outline-variant shadow-elevation-lg max-w-md w-full p-6 space-y-5 relative">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-full hover:bg-brand-surface-dim text-brand-on-surface-variant transition-all"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-primary/10 text-brand-primary text-xs font-bold font-mono">
            <Plus className="w-3.5 h-3.5" />
            <span>Academic Deadline Manager</span>
          </div>
          <h3 className="text-xl font-black text-brand-secondary">Add New Event</h3>
          <p className="text-xs text-brand-on-surface-variant">
            Adds an upcoming deadline directly to your workload calculation feed.
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-brand-secondary">Event Title</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Midterm Exam, Problem Set 3"
              className="w-full px-4 py-2.5 rounded-2xl bg-brand-surface-dim border border-brand-outline-variant text-xs text-brand-secondary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-brand-secondary">Course Code</label>
              <input
                type="text"
                value={courseCode}
                onChange={(e) => setCourseCode(e.target.value)}
                placeholder="e.g. CS101"
                className="w-full px-4 py-2.5 rounded-2xl bg-brand-surface-dim border border-brand-outline-variant text-xs text-brand-secondary focus:outline-none focus:border-brand-primary font-mono uppercase"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-brand-secondary">Event Type</label>
              <select
                value={eventType}
                onChange={(e) => setEventType(e.target.value as any)}
                className="w-full px-4 py-2.5 rounded-2xl bg-brand-surface-dim border border-brand-outline-variant text-xs text-brand-secondary focus:outline-none focus:border-brand-primary"
              >
                <option value="exam">Exam (High Stress)</option>
                <option value="project">Project / Milestone</option>
                <option value="quiz">Quiz</option>
                <option value="assignment">Assignment</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-brand-secondary">Due Date & Time</label>
              <input
                type="datetime-local"
                required
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full px-3 py-2.5 rounded-2xl bg-brand-surface-dim border border-brand-outline-variant text-xs text-brand-secondary focus:outline-none focus:border-brand-primary font-mono"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-brand-secondary">Grade Weight (1-5)</label>
              <input
                type="number"
                step="0.5"
                min="0.5"
                max="5.0"
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                className="w-full px-4 py-2.5 rounded-2xl bg-brand-surface-dim border border-brand-outline-variant text-xs text-brand-secondary focus:outline-none focus:border-brand-primary font-mono"
              />
            </div>
          </div>

          <div className="pt-2 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-full border border-brand-outline-variant text-xs font-bold text-brand-on-surface-variant hover:bg-brand-surface-dim transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 rounded-full bg-brand-primary hover:bg-brand-primary/90 text-white text-xs font-bold transition-all shadow-sm disabled:opacity-50"
            >
              {isSubmitting ? "Adding..." : "Add Event"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

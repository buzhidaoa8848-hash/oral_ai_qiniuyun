"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import type { Profile } from "@/lib/types";
import { fetchProfiles, updateProfile } from "@/lib/api";

const THINKING_STYLES = ["analytical", "creative", "pragmatic", "structured", "intuitive", "collaborative"];
const EXPRESSION_GOALS = [
  "Sound more confident",
  "Be more concise",
  "Use more specific vocabulary",
  "Reduce hedging language",
  "Improve storytelling",
  "Better structure in answers",
];

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ── Form state ────────────────────────────────────────────
  const [identity, setIdentity] = useState("");
  const [experiences, setExperiences] = useState("");
  const [strengths, setStrengths] = useState("");
  const [thinkingStyle, setThinkingStyle] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [expressionGoal, setExpressionGoal] = useState("");

  // ── Load profile ──────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const profiles = await fetchProfiles();
        if (profiles.length > 0) {
          const p = profiles[0];
          setProfile(p);
          setIdentity(p.identity ?? "");
          setExperiences(p.experiences ?? "");
          setStrengths(p.strengths ?? "");
          setThinkingStyle(p.thinking_style ?? "");
          setTargetRole(p.target_role ?? "");
          setExpressionGoal(p.expression_goal ?? "");
        }
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load profile");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // ── Save ──────────────────────────────────────────────────
  const handleSave = useCallback(async () => {
    if (!profile) return;
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const updated = await updateProfile(profile.id, {
        identity,
        experiences,
        strengths,
        thinking_style: thinkingStyle,
        target_role: targetRole,
        expression_goal: expressionGoal,
      });
      setProfile(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }, [profile, identity, experiences, strengths, thinkingStyle, targetRole, expressionGoal]);

  // ── Loading ───────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-zinc-200 border-t-indigo-600" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50">
        <div className="text-center">
          <p className="text-zinc-500">No profile found.</p>
          <button
            onClick={() => router.push("/scenes")}
            className="mt-3 text-sm text-indigo-600 hover:underline"
          >
            Start a scene first
          </button>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-zinc-50">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-2xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900">Your Profile</h1>
            <p className="mt-1 text-sm text-zinc-500">
              Help the AI understand who you are and what you want to improve
            </p>
          </div>
          <button
            onClick={() => router.push("/scenes")}
            className="text-sm text-indigo-600 hover:text-indigo-800"
          >
            ← Back
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-2xl px-6 py-8 space-y-6">
        {/* Identity */}
        <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
          <label className="block text-sm font-semibold text-zinc-700">
            Identity
          </label>
          <p className="text-xs text-zinc-400 mt-0.5 mb-2">
            Who are you? E.g. &ldquo;CS student at NYU, full-stack builder, open-source contributor&rdquo;
          </p>
          <input
            type="text"
            value={identity}
            onChange={(e) => setIdentity(e.target.value)}
            placeholder="CS student, builder, designer..."
            className="w-full rounded-lg border border-zinc-300 px-4 py-2.5 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
        </section>

        {/* Experiences */}
        <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
          <label className="block text-sm font-semibold text-zinc-700">
            Key Experiences
          </label>
          <p className="text-xs text-zinc-400 mt-0.5 mb-2">
            List key projects, roles, or achievements. One per line or comma-separated.
          </p>
          <textarea
            value={experiences}
            onChange={(e) => setExperiences(e.target.value)}
            rows={4}
            placeholder="Built a study-group matching app (React, Node.js)
Led a 5-person team for a hackathon project
Interned at a fintech startup"
            className="w-full rounded-lg border border-zinc-300 px-4 py-2.5 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 resize-y"
          />
        </section>

        {/* Strengths */}
        <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
          <label className="block text-sm font-semibold text-zinc-700">
            Strengths
          </label>
          <p className="text-xs text-zinc-400 mt-0.5 mb-2">
            What are you good at? E.g. &ldquo;problem-solving, debugging, explaining complex ideas&rdquo;
          </p>
          <input
            type="text"
            value={strengths}
            onChange={(e) => setStrengths(e.target.value)}
            placeholder="problem-solving, debugging, clear communication"
            className="w-full rounded-lg border border-zinc-300 px-4 py-2.5 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
        </section>

        {/* Thinking style */}
        <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
          <label className="block text-sm font-semibold text-zinc-700">
            Thinking Style
          </label>
          <p className="text-xs text-zinc-400 mt-0.5 mb-2">
            How do you approach problems?
          </p>
          <div className="flex flex-wrap gap-2">
            {THINKING_STYLES.map((s) => (
              <button
                key={s}
                onClick={() => setThinkingStyle(s)}
                className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                  thinkingStyle === s
                    ? "border-indigo-400 bg-indigo-50 text-indigo-700"
                    : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </section>

        {/* Target role */}
        <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
          <label className="block text-sm font-semibold text-zinc-700">
            Target Role
          </label>
          <p className="text-xs text-zinc-400 mt-0.5 mb-2">
            What role are you practicing for? E.g. &ldquo;intern&rdquo;, &ldquo;founder&rdquo;, &ldquo;manager&rdquo;
          </p>
          <input
            type="text"
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
            placeholder="intern, founder, product manager..."
            className="w-full rounded-lg border border-zinc-300 px-4 py-2.5 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
        </section>

        {/* Expression goal */}
        <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
          <label className="block text-sm font-semibold text-zinc-700">
            Expression Goal
          </label>
          <p className="text-xs text-zinc-400 mt-0.5 mb-2">
            What do you want to improve in your speaking?
          </p>
          <div className="flex flex-wrap gap-2">
            {EXPRESSION_GOALS.map((g) => (
              <button
                key={g}
                onClick={() => setExpressionGoal(g)}
                className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                  expressionGoal === g
                    ? "border-indigo-400 bg-indigo-50 text-indigo-700"
                    : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300"
                }`}
              >
                {g}
              </button>
            ))}
          </div>
        </section>

        {/* Save + feedback */}
        <div className="flex items-center gap-4">
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save Profile"}
          </button>

          {saved && (
            <span className="text-sm text-emerald-600 font-medium animate-in">
              ✓ Profile saved
            </span>
          )}

          {error && (
            <span className="text-sm text-red-600">{error}</span>
          )}
        </div>
      </div>
    </main>
  );
}

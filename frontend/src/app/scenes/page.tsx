"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import type { SceneCard, Profile } from "@/lib/types";
import { DIFFICULTY_COLORS, SCENE_TYPE_ICONS } from "@/lib/types";
import { fetchScenes, fetchProfiles, createProfile, createSession } from "@/lib/api";

export default function ScenesPage() {
  const router = useRouter();
  const [scenes, setScenes] = useState<SceneCard[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  // ── Bootstrap: load scenes + ensure a demo profile exists ─────
  useEffect(() => {
    (async () => {
      try {
        const [scenesData, profiles] = await Promise.all([
          fetchScenes(),
          fetchProfiles(),
        ]);
        setScenes(scenesData);

        let p: Profile;
        if (profiles.length > 0) {
          p = profiles[0];
        } else {
          p = await createProfile("Demo Learner");
        }
        setProfile(p);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load scenes");
      }
    })();
  }, []);

  // ── Click handler: create session → navigate to practice ──────
  const handleSelectScene = useCallback(
    async (scene: SceneCard) => {
      if (!profile) return;
      setLoading((prev) => ({ ...prev, [scene.id]: true }));
      try {
        const session = await createSession(profile.id, scene.id);
        router.push(`/practice/${session.id}`);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to start session");
        setLoading((prev) => ({ ...prev, [scene.id]: false }));
      }
    },
    [profile, router]
  );

  // ── Render ────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50">
        <div className="rounded-xl border border-red-200 bg-red-50 p-8 text-center">
          <p className="text-lg font-semibold text-red-700">Something went wrong</p>
          <p className="mt-2 text-sm text-red-600">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-zinc-50">
      {/* Header */}
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-zinc-900">
              SceneTalk AI
            </h1>
            <p className="mt-1 text-sm text-zinc-500">
              Choose a scene to start practicing
            </p>
          </div>
          {profile && (
            <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">
              {profile.cefr_level || profile.proficiency_level}
            </span>
          )}
        </div>
      </header>

      {/* Card grid */}
      <section className="mx-auto max-w-5xl px-6 py-10">
        {scenes.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-zinc-200 border-t-indigo-600" />
            <p className="mt-4 text-sm text-zinc-500">Loading scenes…</p>
          </div>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2">
            {scenes.map((scene) => (
              <button
                key={scene.id}
                onClick={() => handleSelectScene(scene)}
                disabled={!!loading[scene.id]}
                className="group flex flex-col rounded-2xl border border-zinc-200 bg-white p-6 text-left shadow-sm transition hover:shadow-md hover:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-60"
              >
                {/* Card header */}
                <div className="flex items-start justify-between">
                  <span className="text-3xl">
                    {SCENE_TYPE_ICONS[scene.scene_type] ?? "💬"}
                  </span>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                      DIFFICULTY_COLORS[scene.difficulty] ?? "bg-zinc-100 text-zinc-700"
                    }`}
                  >
                    {scene.difficulty}
                  </span>
                </div>

                {/* Title & description */}
                <h2 className="mt-4 text-lg font-semibold text-zinc-900 group-hover:text-indigo-700">
                  {scene.title}
                </h2>
                <p className="mt-1 line-clamp-2 text-sm text-zinc-500">
                  {scene.task_goal || scene.prompt}
                </p>

                {/* Meta row */}
                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <span className="rounded-md bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600">
                    {scene.style}
                  </span>
                  <span className="rounded-md bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600">
                    {scene.scene_type}
                  </span>
                  {scene.tags?.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="rounded-md bg-zinc-100 px-2 py-0.5 text-xs text-zinc-500"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                {/* Loading indicator on button */}
                {loading[scene.id] && (
                  <div className="mt-4 flex items-center gap-2 text-sm text-indigo-600">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" />
                    Starting session…
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

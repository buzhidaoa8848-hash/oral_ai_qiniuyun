"use client";

import { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import type { Material, SceneCard } from "@/lib/types";
import { DIFFICULTY_COLORS, SCENE_TYPE_ICONS } from "@/lib/types";
import {
  createMaterialFromPaste,
  uploadMaterialFile,
  generateScene,
  fetchProfiles,
  createProfile,
  createSession,
} from "@/lib/api";

const SCENE_TYPES = ["conversation", "interview", "restaurant", "meeting", "pitch"];
const STYLES = ["casual", "semi-formal", "professional"];
const LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];

export default function MaterialsPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Form state ───────────────────────────────────────────
  const [title, setTitle] = useState("");
  const [rawText, setRawText] = useState("");
  const [sourceType, setSourceType] = useState("paste");
  const [sceneType, setSceneType] = useState("conversation");
  const [style, setStyle] = useState("casual");
  const [userLevel, setUserLevel] = useState("B1");
  const [targetGoal, setTargetGoal] = useState("");

  // ── Flow state ───────────────────────────────────────────
  const [material, setMaterial] = useState<Material | null>(null);
  const [generatedScene, setGeneratedScene] = useState<SceneCard | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // ── Paste handler ────────────────────────────────────────
  const handlePaste = useCallback(async () => {
    if (!title.trim() || !rawText.trim()) {
      setError("Title and text are required");
      return;
    }
    setError(null);
    setLoading("paste");
    try {
      const mat = await createMaterialFromPaste({
        title: title.trim(),
        raw_text: rawText.trim(),
        source_type: "paste",
      });
      setMaterial(mat);
      setSourceType("paste");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to save material");
    } finally {
      setLoading(null);
    }
  }, [title, rawText]);

  // ── Upload handler ───────────────────────────────────────
  const handleUpload = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      setError(null);
      setLoading("upload");
      try {
        const mat = await uploadMaterialFile(file);
        setMaterial(mat);
        setTitle(mat.title);
        setRawText(mat.raw_text);
        setSourceType(mat.source_type);
      } catch (e: unknown) {
        setError(
          e instanceof Error ? e.message : "Upload failed — check file type"
        );
      } finally {
        setLoading(null);
      }
    },
    []
  );

  // ── Generate scene ───────────────────────────────────────
  const handleGenerate = useCallback(async () => {
    if (!material) return;
    setError(null);
    setLoading("generate");
    try {
      const result = await generateScene(material.id, {
        scene_type: sceneType,
        style,
        user_level: userLevel,
        target_goal: targetGoal,
      });
      setGeneratedScene(result.scene);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setLoading(null);
    }
  }, [material, sceneType, style, userLevel, targetGoal]);

  // ── Start practice with generated scene ──────────────────
  const handleStartPractice = useCallback(async () => {
    if (!generatedScene) return;
    setLoading("practice");
    try {
      const profiles = await fetchProfiles();
      let profileId: string;
      if (profiles.length > 0) {
        profileId = profiles[0].id;
      } else {
        const p = await createProfile("Demo Learner");
        profileId = p.id;
      }
      const session = await createSession(profileId, generatedScene.id);
      router.push(`/practice/${session.id}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to start practice");
      setLoading(null);
    }
  }, [generatedScene, router]);

  // ── Render ───────────────────────────────────────────────
  const levelColor =
    DIFFICULTY_COLORS[generatedScene?.difficulty ?? ""] ??
    "bg-zinc-100 text-zinc-700";

  return (
    <main className="min-h-screen bg-zinc-50">
      {/* Header */}
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-zinc-900">
              Material Import
            </h1>
            <p className="mt-1 text-sm text-zinc-500">
              Paste a transcript or upload a file, then generate a SceneCard
            </p>
          </div>
          <button
            onClick={() => router.push("/scenes")}
            className="text-sm text-indigo-600 hover:text-indigo-800"
          >
            ← Built-in scenes
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-4xl px-6 py-8 space-y-8">
        {/* ── Step 1: Source material ─────────────────────── */}
        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-zinc-800">
            Step 1 — Source Material
          </h2>

          <div className="mt-4 space-y-4">
            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-zinc-600">
                Title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. English conversation transcript"
                className="mt-1 w-full rounded-lg border border-zinc-300 px-4 py-2.5 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
              />
            </div>

            {/* Text area */}
            <div>
              <label className="block text-sm font-medium text-zinc-600">
                Paste text (transcript / dialogue / article)
              </label>
              <textarea
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                rows={8}
                placeholder="Paste your conversation transcript, dialogue, or article here…"
                className="mt-1 w-full rounded-lg border border-zinc-300 px-4 py-3 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 resize-y"
              />
            </div>

            {/* Actions */}
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={handlePaste}
                disabled={loading === "paste" || !title || !rawText}
                className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading === "paste" ? "Saving…" : "Save Pasted Text"}
              </button>

              <span className="text-sm text-zinc-400">or</span>

              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={loading === "upload"}
                className="rounded-lg border border-zinc-300 bg-white px-5 py-2.5 text-sm font-semibold text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
              >
                {loading === "upload" ? "Uploading…" : "Upload File"}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.md,.srt,.vtt"
                onChange={handleUpload}
                className="hidden"
              />
              <span className="text-xs text-zinc-400">.txt .md .srt .vtt</span>
            </div>

            {/* Material saved indicator */}
            {material && (
              <div className="flex items-center gap-2 rounded-lg bg-emerald-50 px-4 py-2 text-sm text-emerald-700">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                Material saved: <strong>{material.title}</strong>
                <span className="text-emerald-500">
                  ({material.source_type}, {(material.raw_text?.length ?? 0).toLocaleString()} chars)
                </span>
              </div>
            )}
          </div>
        </section>

        {/* ── Step 2: Scene config ────────────────────────── */}
        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-zinc-800">
            Step 2 — Scene Configuration
          </h2>

          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Scene type */}
            <div>
              <label className="block text-sm font-medium text-zinc-600">
                Scene Type
              </label>
              <select
                value={sceneType}
                onChange={(e) => setSceneType(e.target.value)}
                className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2.5 text-sm focus:border-indigo-400 focus:outline-none"
              >
                {SCENE_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {SCENE_TYPE_ICONS[t] ?? "💬"} {t}
                  </option>
                ))}
              </select>
            </div>

            {/* Style */}
            <div>
              <label className="block text-sm font-medium text-zinc-600">
                Style
              </label>
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2.5 text-sm focus:border-indigo-400 focus:outline-none"
              >
                {STYLES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            {/* User level */}
            <div>
              <label className="block text-sm font-medium text-zinc-600">
                User Level
              </label>
              <select
                value={userLevel}
                onChange={(e) => setUserLevel(e.target.value)}
                className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2.5 text-sm focus:border-indigo-400 focus:outline-none"
              >
                {LEVELS.map((l) => (
                  <option key={l} value={l}>
                    {l}
                  </option>
                ))}
              </select>
            </div>

            {/* Target goal */}
            <div>
              <label className="block text-sm font-medium text-zinc-600">
                Target Goal
              </label>
              <input
                type="text"
                value={targetGoal}
                onChange={(e) => setTargetGoal(e.target.value)}
                placeholder="e.g. Practice ordering food"
                className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2.5 text-sm focus:border-indigo-400 focus:outline-none"
              />
            </div>
          </div>

          {/* Generate button */}
          <button
            onClick={handleGenerate}
            disabled={!material || loading === "generate"}
            className="mt-5 rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading === "generate" ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                Generating…
              </span>
            ) : (
              "Generate SceneCard"
            )}
          </button>
        </section>

        {/* ── Error ───────────────────────────────────────── */}
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-3 underline hover:no-underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* ── Step 3: Preview ─────────────────────────────── */}
        {generatedScene && (
          <section className="rounded-2xl border border-indigo-200 bg-white p-6 shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-lg font-semibold text-zinc-800">
                  Step 3 — Generated SceneCard Preview
                </h2>
                <p className="mt-1 text-sm text-zinc-500">
                  Review the AI-generated scene below. You can start practicing
                  or go back to adjust the config.
                </p>
              </div>
              <button
                onClick={handleStartPractice}
                disabled={loading === "practice"}
                className="rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
              >
                {loading === "practice" ? "Starting…" : "Start Practice →"}
              </button>
            </div>

            {/* Scene preview card */}
            <div className="mt-6 rounded-xl border border-zinc-200 bg-zinc-50/50 p-5 space-y-5">
              {/* Title row */}
              <div className="flex items-center gap-3">
                <span className="text-3xl">
                  {SCENE_TYPE_ICONS[generatedScene.scene_type] ?? "💬"}
                </span>
                <div>
                  <h3 className="text-xl font-bold text-zinc-900">
                    {generatedScene.title}
                  </h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span
                      className={`rounded-full px-2.5 py-0 text-xs font-semibold ${levelColor}`}
                    >
                      {generatedScene.difficulty}
                    </span>
                    <span className="text-xs text-zinc-400">·</span>
                    <span className="text-xs text-zinc-500 capitalize">
                      {generatedScene.style}
                    </span>
                    <span className="text-xs text-zinc-400">·</span>
                    <span className="text-xs text-zinc-500 capitalize">
                      {generatedScene.scene_type}
                    </span>
                  </div>
                </div>
              </div>

              {/* Roles */}
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg border border-indigo-100 bg-indigo-50/50 p-3">
                  <p className="text-xs font-semibold text-indigo-500">
                    Your Role
                  </p>
                  <p className="text-sm font-medium text-indigo-900">
                    {generatedScene.user_role}
                  </p>
                </div>
                <div className="rounded-lg border border-amber-100 bg-amber-50/50 p-3">
                  <p className="text-xs font-semibold text-amber-600">
                    AI Role
                  </p>
                  <p className="text-sm font-medium text-amber-900">
                    {generatedScene.ai_role}
                  </p>
                </div>
              </div>

              {/* Task goal */}
              <div>
                <p className="text-xs font-semibold text-zinc-400">
                  Task Goal
                </p>
                <p className="mt-1 text-sm text-zinc-700">
                  {generatedScene.task_goal}
                </p>
              </div>

              {/* Opening question */}
              <div className="rounded-lg border border-zinc-200 bg-white p-4">
                <p className="text-xs font-semibold text-zinc-400">
                  Opening Question
                </p>
                <p className="mt-1 text-base italic text-zinc-700">
                  &ldquo;{generatedScene.opening_question}&rdquo;
                </p>
              </div>

              {/* Key expressions */}
              {generatedScene.key_expressions &&
                generatedScene.key_expressions.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-zinc-400">
                      Key Expressions
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {generatedScene.key_expressions.map((expr, i) => (
                        <span
                          key={i}
                          className="rounded-lg border border-zinc-200 bg-white px-3 py-1 text-xs text-zinc-700"
                        >
                          {expr}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

              {/* Must cover */}
              {generatedScene.must_cover_points &&
                generatedScene.must_cover_points.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-zinc-400">
                      Must Cover
                    </p>
                    <ol className="mt-2 space-y-1">
                      {generatedScene.must_cover_points.map((pt, i) => (
                        <li
                          key={i}
                          className="flex items-start gap-2 text-sm text-zinc-700"
                        >
                          <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-700">
                            {i + 1}
                          </span>
                          {pt}
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

              {/* Evaluation */}
              <div>
                <p className="text-xs font-semibold text-zinc-400">
                  Evaluation Rubric
                </p>
                <p className="mt-1 text-sm text-zinc-600">
                  {generatedScene.evaluation_rubric}
                </p>
              </div>

              {/* Tags */}
              {generatedScene.tags && generatedScene.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {generatedScene.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-md bg-zinc-100 px-2 py-0.5 text-xs text-zinc-500"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

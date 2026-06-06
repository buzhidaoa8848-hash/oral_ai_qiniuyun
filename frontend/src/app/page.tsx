"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import type { SceneCard, Profile } from "@/lib/types";
import { DIFFICULTY_COLORS, SCENE_TYPE_ICONS } from "@/lib/types";
import {
  fetchScenes,
  fetchProfiles,
  createProfile,
  updateProfile,
  createSession,
  createMaterialFromPaste,
  generateScene,
} from "@/lib/api";

// ── Constants ──────────────────────────────────────────────────
const IDENTITIES = [
  { key: "primary_school", label: "Primary School Student", emoji: "🧒" },
  { key: "middle_school", label: "Middle School Student", emoji: "👦" },
  { key: "high_school", label: "High School Student", emoji: "🧑" },
  { key: "college", label: "College Student", emoji: "🎓" },
  { key: "working_professional", label: "Working Professional", emoji: "💼" },
];
const CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];
const STYLES = [
  { key: "friendly", label: "Friendly", emoji: "😊", desc: "Warm and supportive" },
  { key: "professional", label: "Professional", emoji: "👔", desc: "Formal and structured" },
  { key: "strict", label: "Strict", emoji: "🎯", desc: "Pushes you hard" },
  { key: "high_pressure", label: "High-pressure", emoji: "🔥", desc: "Intense and fast-paced" },
  { key: "harsh_but_professional", label: "Harsh but professional", emoji: "🫡", desc: "Blunt but fair" },
  { key: "encouraging", label: "Encouraging", emoji: "🌟", desc: "Positive and motivating" },
];
const SCENE_RECS: Record<string, string[]> = {
  primary_school: ["Restaurant Ordering"],
  middle_school: ["Restaurant Ordering"],
  high_school: ["Internship Interview", "Restaurant Ordering", "Project Pitch Q&A"],
  college: ["Internship Interview", "Project Pitch Q&A", "Work Meeting"],
  working_professional: ["Work Meeting", "Internship Interview", "Project Pitch Q&A"],
};

function cefrFromTest(scores: Record<string, number | null>): string | null {
  if (scores.ielts_score) {
    const s = scores.ielts_score;
    if (s >= 8) return "C2"; if (s >= 7) return "C1"; if (s >= 6) return "B2"; if (s >= 5) return "B1"; return "A2";
  }
  if (scores.toefl_score) {
    const s = scores.toefl_score;
    if (s >= 110) return "C2"; if (s >= 100) return "C1"; if (s >= 80) return "B2"; if (s >= 60) return "B1"; return "A2";
  }
  if (scores.cet6_score) { if (scores.cet6_score >= 550) return "C1"; if (scores.cet6_score >= 425) return "B2"; return "B1"; }
  if (scores.cet4_score) { if (scores.cet4_score >= 550) return "B2"; if (scores.cet4_score >= 425) return "B1"; return "A2"; }
  if (scores.gaokao_english_score) { const s = scores.gaokao_english_score; if (s >= 135) return "B2"; if (s >= 120) return "B1"; if (s >= 100) return "A2"; return "A1"; }
  if (scores.zhongkao_english_score) { const s = scores.zhongkao_english_score; if (s >= 115) return "B1"; if (s >= 100) return "A2"; return "A1"; }
  return null;
}

export default function HomePage() {
  const router = useRouter();

  // ── State ────────────────────────────────────────────────
  const [identity, setIdentity] = useState<string>("");
  const [cefr, setCefr] = useState<string>("B1");
  const [estimatedLevel, setEstimatedLevel] = useState<string | null>(null);
  const [testScores, setTestScores] = useState<Record<string, string>>({});
  const [style, setStyle] = useState<string>("professional");
  const [scenes, setScenes] = useState<SceneCard[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  // Modal state
  const [detailScene, setDetailScene] = useState<SceneCard | null>(null);
  const [customMaterial, setCustomMaterial] = useState("");
  const [customSceneId, setCustomSceneId] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── Bootstrap ────────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const [sData, pArr] = await Promise.all([fetchScenes(), fetchProfiles()]);
        setScenes(sData);
        let p: Profile;
        if (pArr.length > 0) {
          p = pArr[0];
        } else {
          p = await createProfile("Learner");
        }
        setProfile(p);
        setIdentity(p.learner_identity || "");
        setCefr(p.cefr_level || "B1");
        if (p.ielts_score) setTestScores(prev => ({ ...prev, ielts_score: String(p.ielts_score) }));
        if (p.toefl_score) setTestScores(prev => ({ ...prev, toefl_score: String(p.toefl_score) }));
        if (p.cet4_score) setTestScores(prev => ({ ...prev, cet4_score: String(p.cet4_score) }));
        if (p.cet6_score) setTestScores(prev => ({ ...prev, cet6_score: String(p.cet6_score) }));
        if (p.gaokao_english_score) setTestScores(prev => ({ ...prev, gaokao_english_score: String(p.gaokao_english_score) }));
        if (p.zhongkao_english_score) setTestScores(prev => ({ ...prev, zhongkao_english_score: String(p.zhongkao_english_score) }));
      } catch { /* defaults */ }
    })();
  }, []);

  // ── Auto-save profile when identity / cefr / testScores change ─
  const doSave = useCallback(async (
    ident: string, lvl: string, scores: Record<string, string>, prof: Profile | null
  ) => {
    if (!prof) return;
    try {
      const numeric: Record<string, number | null> = {};
      for (const [k, v] of Object.entries(scores)) numeric[k] = v ? parseFloat(v) : null;
      const updated = await updateProfile(prof.id, {
        learner_identity: ident || null,
        cefr_level: lvl,
        proficiency_level: lvl,  // sync old field too
        ...numeric,
      } as Partial<Profile>);
      setProfile(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 1800);
    } catch {
      // silently retry next change
    }
  }, []);

  useEffect(() => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => doSave(identity, cefr, testScores, profile), 500);
    return () => { if (saveTimer.current) clearTimeout(saveTimer.current); };
  }, [identity, cefr, testScores]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Test scores → estimated level ───────────────────────
  const handleTestScoreChange = useCallback((key: string, value: string) => {
    const newScores = { ...testScores, [key]: value };
    setTestScores(newScores);
    const numeric: Record<string, number | null> = {};
    for (const [k, v] of Object.entries(newScores)) numeric[k] = v ? parseFloat(v) : null;
    setEstimatedLevel(cefrFromTest(numeric));
  }, [testScores]);

  // ── Scene recommendations ───────────────────────────────
  const recOrder = SCENE_RECS[identity] || [];
  const sortedScenes = [...scenes].sort((a, b) => {
    const ai = recOrder.indexOf(a.title), bi = recOrder.indexOf(b.title);
    if (ai >= 0 && bi >= 0) return ai - bi;
    if (ai >= 0) return -1; if (bi >= 0) return 1;
    const diffOrder = ["A2","A1","B1","B2","C1","C2"];
    return diffOrder.indexOf(a.difficulty) - diffOrder.indexOf(b.difficulty);
  });

  // ── Start practice ──────────────────────────────────────
  const startPractice = useCallback(async (sceneId: string) => {
    if (!profile) return;
    setLoading(true); setError(null);
    try {
      const session = await createSession(profile.id, sceneId);
      router.push(`/practice/${session.id}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to start");
      setLoading(false);
    }
  }, [profile, router]);

  // ── Generate custom scene from material ─────────────────
  const handleCustomize = useCallback(async () => {
    if (!customMaterial.trim() || !detailScene) return;
    setGenerating(true); setError(null);
    try {
      const mat = await createMaterialFromPaste({ title: detailScene.title + " (custom)", raw_text: customMaterial.trim() });
      const gen = await generateScene(mat.id, { scene_type: detailScene.scene_type, style, user_level: cefr, target_goal: detailScene.task_goal });
      setCustomSceneId(gen.scene_card_id);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Generation failed");
    } finally { setGenerating(false); }
  }, [customMaterial, detailScene, style, cefr]);

  // ── Modal helpers ───────────────────────────────────────
  const openDetail = (scene: SceneCard) => { setDetailScene(scene); setCustomMaterial(""); setCustomSceneId(null); };
  const closeDetail = () => setDetailScene(null);
  const activeSceneId = customSceneId || detailScene?.id || null;

  return (
    <main className="min-h-screen bg-zinc-50">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto max-w-3xl px-6 py-5 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-zinc-900">SceneTalk AI</h1>
            <p className="mt-1 text-sm text-zinc-500">Practice spoken English through realistic scene-based conversations</p>
          </div>
          {saved && <span className="text-xs text-emerald-600 font-medium animate-in">✓ Saved</span>}
        </div>
      </header>

      <div className="mx-auto max-w-3xl px-6 py-8 space-y-8">
        {/* ── Step 1: Identity ────────────────────────────── */}
        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-zinc-800">Step 1 — Who are you?</h2>
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {IDENTITIES.map((id) => (
              <button key={id.key} onClick={() => setIdentity(id.key)}
                className={`flex flex-col items-center gap-1.5 rounded-xl border p-4 text-center transition-all ${
                  identity === id.key ? "border-indigo-400 bg-indigo-50 ring-2 ring-indigo-100" : "border-zinc-200 hover:border-zinc-300 hover:bg-zinc-50"
                }`}>
                <span className="text-2xl">{id.emoji}</span>
                <span className="text-xs font-medium text-zinc-700 leading-tight">{id.label}</span>
              </button>
            ))}
          </div>
        </section>

        {/* ── Step 2: CEFR + Test Scores ──────────────────── */}
        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-zinc-800">Step 2 — What is your English level?</h2>
          <div className="mt-4">
            <p className="text-sm font-medium text-zinc-600 mb-2">CEFR Level</p>
            <div className="flex gap-2">
              {CEFR_LEVELS.map((l) => (
                <button key={l} onClick={() => setCefr(l)}
                  className={`flex-1 rounded-lg border py-2 text-sm font-semibold transition-all ${
                    cefr === l ? "border-indigo-400 bg-indigo-50 text-indigo-700" : "border-zinc-200 text-zinc-600 hover:border-zinc-300"
                  }`}>{l}</button>
              ))}
            </div>
          </div>
          <div className="mt-5">
            <p className="text-sm font-medium text-zinc-600 mb-2">Test Scores (optional — fill any one)</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[["ielts_score","IELTS (0–9)"],["toefl_score","TOEFL iBT"],["cet4_score","CET-4"],["cet6_score","CET-6"],["gaokao_english_score","Gaokao English"],["zhongkao_english_score","Zhongkao English"]].map(([key,label]) => (
                <div key={key}><label className="block text-xs text-zinc-400 mb-1">{label}</label>
                  <input type="number" step="0.5" value={testScores[key]||""} onChange={e => handleTestScoreChange(key, e.target.value)} placeholder="—"
                    className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none" /></div>
              ))}
            </div>
          </div>
          {estimatedLevel && (
            <div className="mt-3 rounded-lg bg-amber-50 border border-amber-200 px-4 py-2 text-sm text-amber-800">
              Estimated CEFR from your test scores: <strong>{estimatedLevel}</strong>
              <span className="ml-1 text-amber-500">(your manual selection takes priority)</span>
            </div>
          )}
        </section>

        {/* ── Step 3: Scene cards ──────────────────────────── */}
        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-zinc-800">Step 3 — Choose a scene</h2>
          <p className="mt-1 text-sm text-zinc-500">Click any card to view details and optionally add your own material.</p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {sortedScenes.map((scene) => {
              const isRec = recOrder.includes(scene.title);
              return (
                <button key={scene.id} onClick={() => openDetail(scene)}
                  className="flex items-start gap-3 rounded-xl border border-zinc-200 p-4 text-left hover:border-indigo-300 hover:shadow-sm transition-all">
                  <span className="text-2xl">{SCENE_TYPE_ICONS[scene.scene_type] ?? "💬"}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-zinc-800">{scene.title}</span>
                      {isRec && <span className="text-[10px] bg-amber-100 text-amber-700 rounded px-1.5 py-0.5">Recommended</span>}
                    </div>
                    <p className="text-xs text-zinc-500 mt-0.5 line-clamp-2">{scene.task_goal || scene.prompt}</p>
                    <span className={`inline-block mt-1.5 rounded-full px-2 py-0 text-[10px] font-semibold ${DIFFICULTY_COLORS[scene.difficulty] ?? "bg-zinc-100 text-zinc-700"}`}>
                      {scene.difficulty} · {scene.scene_type}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {/* ── Error ────────────────────────────────────────── */}
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-xs underline">Dismiss</button>
          </div>
        )}

        {/* ── Footer links ─────────────────────────────────── */}
        <div className="flex justify-center gap-4 text-xs text-zinc-400 pb-12">
          <a href="/scenes" className="hover:text-indigo-600 underline">All Scenes</a>
          <span>·</span>
          <a href="/materials" className="hover:text-indigo-600 underline">Materials</a>
          <span>·</span>
          <a href="/profile" className="hover:text-indigo-600 underline">Profile</a>
        </div>
      </div>

      {/* ── Scene Detail Modal ─────────────────────────────── */}
      {detailScene && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] bg-black/40" onClick={closeDetail}>
          <div className="mx-4 w-full max-w-lg max-h-[80vh] overflow-y-auto rounded-2xl bg-white shadow-2xl" onClick={e => e.stopPropagation()}>
            {/* Header */}
            <div className="sticky top-0 bg-white border-b border-zinc-100 px-6 py-4 flex items-center gap-3">
              <span className="text-2xl">{SCENE_TYPE_ICONS[detailScene.scene_type] ?? "💬"}</span>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-zinc-900">{detailScene.title}</h3>
                <span className={`inline-block mt-0.5 rounded-full px-2 py-0 text-[10px] font-semibold ${DIFFICULTY_COLORS[detailScene.difficulty] ?? "bg-zinc-100 text-zinc-700"}`}>
                  {detailScene.difficulty} · {detailScene.scene_type} · {detailScene.style}
                </span>
              </div>
              <button onClick={closeDetail} className="text-zinc-400 hover:text-zinc-600 text-xl leading-none">&times;</button>
            </div>

            {/* Body */}
            <div className="px-6 py-5 space-y-4">
              {/* Roles */}
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg border border-indigo-100 bg-indigo-50/50 p-3">
                  <p className="text-[10px] font-semibold text-indigo-500 uppercase">Your Role</p>
                  <p className="text-sm font-medium text-indigo-900">{detailScene.user_role}</p>
                </div>
                <div className="rounded-lg border border-amber-100 bg-amber-50/50 p-3">
                  <p className="text-[10px] font-semibold text-amber-600 uppercase">AI Role</p>
                  <p className="text-sm font-medium text-amber-900">{detailScene.ai_role}</p>
                </div>
              </div>

              {/* Task goal */}
              <div><p className="text-xs font-semibold text-zinc-400 uppercase">Task Goal</p>
                <p className="mt-1 text-sm text-zinc-700">{detailScene.task_goal}</p></div>

              {/* Opening question */}
              <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-3">
                <p className="text-xs font-semibold text-zinc-400 uppercase">Opening Question</p>
                <p className="mt-1 text-sm italic text-zinc-700">&ldquo;{detailScene.opening_question}&rdquo;</p>
              </div>

              {/* Key expressions */}
              {detailScene.key_expressions && detailScene.key_expressions.length > 0 && (
                <div><p className="text-xs font-semibold text-zinc-400 uppercase">Key Expressions</p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {detailScene.key_expressions.map((e,i) => (<span key={i} className="rounded-md border border-zinc-200 bg-white px-2 py-1 text-[11px] text-zinc-600">{e}</span>))}
                  </div></div>
              )}

              {/* Must cover */}
              {detailScene.must_cover_points && detailScene.must_cover_points.length > 0 && (
                <div><p className="text-xs font-semibold text-zinc-400 uppercase">Must Cover</p>
                  <ol className="mt-1.5 space-y-1">
                    {detailScene.must_cover_points.map((p,i) => (<li key={i} className="flex items-start gap-2 text-xs text-zinc-600"><span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-[10px] font-bold text-indigo-600">{i+1}</span>{p}</li>))}
                  </ol></div>
              )}

              {/* ── Customize section ───────────────────────── */}
              <div className="border-t border-zinc-100 pt-4">
                <p className="text-sm font-semibold text-zinc-700 mb-2">Customize this scene with your own material</p>
                <textarea value={customMaterial} onChange={e => setCustomMaterial(e.target.value)}
                  rows={3}
                  placeholder="Paste YouTube subtitles, Xiaohongshu notes, Bilibili notes, interview scripts, course materials, or your own learning notes here."
                  className="w-full rounded-xl border border-zinc-300 px-4 py-2.5 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 resize-y" />
                {customMaterial.trim() && (
                  <button onClick={handleCustomize} disabled={generating}
                    className="mt-2 rounded-lg border border-indigo-300 bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700 hover:bg-indigo-100 disabled:opacity-50">
                    {generating ? "Generating…" : "📝 Customize with My Material"}
                  </button>
                )}
                {customSceneId && (
                  <div className="mt-2 rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-2 text-sm text-emerald-700">
                    ✓ Custom scene generated! You&apos;ll practice with your tailored version.
                  </div>
                )}
              </div>

              {/* Style picker */}
              <div className="border-t border-zinc-100 pt-4">
                <p className="text-xs font-semibold text-zinc-400 uppercase mb-2">Scene Style</p>
                <div className="flex flex-wrap gap-2">
                  {STYLES.map(s => (
                    <button key={s.key} onClick={() => setStyle(s.key)}
                      className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-all ${style === s.key ? "border-indigo-400 bg-indigo-50 text-indigo-700" : "border-zinc-200 text-zinc-600 hover:border-zinc-300"}`}>
                      {s.emoji} {s.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="sticky bottom-0 bg-white border-t border-zinc-100 px-6 py-4 flex items-center gap-3">
              <button onClick={closeDetail}
                className="rounded-lg border border-zinc-300 px-4 py-2.5 text-sm font-medium text-zinc-600 hover:bg-zinc-50">← Back</button>
              <button onClick={() => activeSceneId && startPractice(activeSceneId)} disabled={loading || !activeSceneId}
                className="flex-1 rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-bold text-white hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed">
                {loading ? "Starting…" : "▶ Start This Practice"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

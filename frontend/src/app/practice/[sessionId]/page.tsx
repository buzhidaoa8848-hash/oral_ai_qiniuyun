"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import type { SceneCard, PracticeSession, ConversationTurn, LatencySnapshot, PronunciationResult } from "@/lib/types";
import { DIFFICULTY_COLORS, SCENE_TYPE_ICONS } from "@/lib/types";
import { fetchSession, fetchScene, fetchTurns, postTurn, voiceTurn, finishSession } from "@/lib/api";
import VoiceRecorder from "@/components/VoiceRecorder";
import LiveLatencyPanel from "@/components/LiveLatencyPanel";
import CorrectionHintPanel from "@/components/CorrectionHintPanel";
import type { EvaluationScores } from "@/lib/types";

export default function PracticePage() {
  const params = useParams<{ sessionId: string }>();
  const router = useRouter();

  // ── Data state ────────────────────────────────────────────
  const [session, setSession] = useState<PracticeSession | null>(null);
  const [scene, setScene] = useState<SceneCard | null>(null);
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // ── Voice state ───────────────────────────────────────────
  const [latency, setLatency] = useState<LatencySnapshot | null>(null);
  const [turnStatus, setTurnStatus] = useState<"idle" | "recording" | "transcribing" | "llm" | "tts" | "complete">("idle");
  const [latestHints, setLatestHints] = useState<string[]>([]);
  const [latestScores, setLatestScores] = useState<EvaluationScores | null>(null);
  const [latestPron, setLatestPron] = useState<PronunciationResult | null>(null);
  const [sttDegraded, setSttDegraded] = useState(false);
  const [finishing, setFinishing] = useState(false);

  // ── Input state ───────────────────────────────────────────
  const [input, setInput] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // ── Bootstrap ─────────────────────────────────────────────
  useEffect(() => {
    if (!params?.sessionId) return;
    (async () => {
      try {
        const [s, sc, t] = await Promise.all([
          fetchSession(params.sessionId),
          fetchScene(""), // will be replaced after we get session
          fetchTurns(params.sessionId),
        ]);
        setSession(s);
        const card = await fetchScene(s.scene_card_id);
        setScene(card);
        setTurns(t);
        // If no turns yet, auto-send opening_question as first AI message
        if (t.length === 0 && card.opening_question) {
          setTurns([
            {
              id: "opening",
              session_id: s.id,
              turn_index: 0,
              role: "ai",
              message: card.opening_question,
              intent: "open_conversation",
              based_on_user_point: null,
              next_goal: card.must_cover_points?.[0] ?? null,
              should_interrupt: false,
              audio_url: null,
              transcript: null,
              created_at: new Date().toISOString(),
            },
          ]);
        }
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    })();
  }, [params?.sessionId]);

  // ── Auto-scroll ───────────────────────────────────────────
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  // ── Send message ──────────────────────────────────────────
  const handleSend = useCallback(async () => {
    const msg = input.trim();
    if (!msg || sending || !params?.sessionId) return;
    setInput("");
    setSending(true);

    // Optimistically add user turn
    const optId = "opt-" + Date.now();
    setTurns((prev) => [
      ...prev,
      {
        id: optId,
        session_id: params.sessionId,
        turn_index: prev.length,
        role: "user",
        message: msg,
        intent: null,
        based_on_user_point: null,
        next_goal: null,
        should_interrupt: false,
        audio_url: null,
        transcript: null,
        created_at: new Date().toISOString(),
      },
    ]);

    try {
      const resp = await postTurn(params.sessionId, msg);
      setLatestHints(resp.light_hints ?? []);
      setLatestScores(resp.evaluation ?? null);
      // Replace optimistic user turn + add AI turn
      setTurns((prev) => {
        const filtered = prev.filter((t) => t.id !== optId);
        return [...filtered, resp.user_turn, resp.ai_turn];
      });
      if (resp.is_final) {
        setSession((prev) =>
          prev ? { ...prev, status: "completed" } : prev
        );
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Send failed");
      // Remove optimistic turn on error
      setTurns((prev) => prev.filter((t) => t.id !== optId));
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  }, [input, sending, params?.sessionId]);

  // ── TTS playback ──────────────────────────────────────────
  const speakReply = useCallback((text: string) => {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = 0.95;
    utterance.onend = () => setTurnStatus("complete");
    setTurnStatus("tts");
    const t0 = performance.now();
    utterance.onstart = () => {
      const ttsMs = Math.round(performance.now() - t0);
      setLatency((prev) => prev ? { ...prev, tts_ms: ttsMs } : null);
    };
    window.speechSynthesis.speak(utterance);
  }, []);

  // ── Voice turn handler ─────────────────────────────────────
  const handleVoiceRecording = useCallback(
    async (blob: Blob) => {
      if (!params?.sessionId) return;
      setTurnStatus("transcribing");
      setError(null);
      try {
        const resp = await voiceTurn(params.sessionId, blob);
        setTurnStatus("llm");
        await new Promise((r) => setTimeout(r, 100));
        setLatency(resp.latency);
        setLatestHints(resp.light_hints ?? []);
        setLatestScores(resp.evaluation ?? null);
        setLatestPron(resp.pronunciation ?? null);
        setSttDegraded(resp.stt_degraded ?? false);
        // Add turns
        setTurns((prev) => [...prev, resp.user_turn, resp.ai_turn]);
        if (resp.is_final) {
          setSession((prev) => (prev ? { ...prev, status: "completed" } : prev));
        }
        // Speak the AI reply
        speakReply(resp.reply);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Voice turn failed");
        setTurnStatus("idle");
      }
    },
    [params?.sessionId, speakReply]
  );

  // ── End session → report ──────────────────────────────────
  const handleEndSession = useCallback(async () => {
    if (!params?.sessionId || finishing) return;
    setFinishing(true);
    try {
      await finishSession(params.sessionId);
      router.push(`/report/${params.sessionId}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to finish session");
      setFinishing(false);
    }
  }, [params?.sessionId, finishing, router]);

  // ── Key handler ───────────────────────────────────────────
  const handleKey = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  // ── Loading / Error ───────────────────────────────────────
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-zinc-200 border-t-indigo-600" />
          <p className="mt-4 text-sm text-zinc-500">Loading session…</p>
        </div>
      </div>
    );
  }

  if (error || !scene) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50">
        <div className="rounded-xl border border-red-200 bg-red-50 p-8 text-center">
          <p className="text-lg font-semibold text-red-700">Error</p>
          <p className="mt-2 text-sm text-red-600">{error ?? "Not found"}</p>
          <button
            onClick={() => router.push("/scenes")}
            className="mt-4 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Back to scenes
          </button>
        </div>
      </div>
    );
  }

  const levelColor = DIFFICULTY_COLORS[scene.difficulty] ?? "bg-zinc-100 text-zinc-700";
  const icon = SCENE_TYPE_ICONS[scene.scene_type] ?? "💬";
  const isCompleted = session?.status === "completed";

  return (
    <div className="flex h-screen bg-zinc-50">
      {/* ── Sidebar ──────────────────────────────────────── */}
      <aside className="hidden w-72 shrink-0 flex-col border-r border-zinc-200 bg-white lg:flex">
        {/* Scene info */}
        <div className="border-b border-zinc-100 p-5">
          <div className="flex items-center gap-2.5">
            <span className="text-2xl">{icon}</span>
            <div>
              <h2 className="text-sm font-bold text-zinc-900">{scene.title}</h2>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className={`rounded-full px-2 py-0 text-[10px] font-semibold ${levelColor}`}>
                  {scene.difficulty}
                </span>
                <span className="text-[10px] text-zinc-400 capitalize">{scene.style}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Roles */}
        <div className="border-b border-zinc-100 p-5 space-y-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wide text-indigo-500">
              Your Role
            </p>
            <p className="text-sm font-medium text-zinc-800">{scene.user_role}</p>
          </div>
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wide text-amber-600">
              AI Role
            </p>
            <p className="text-sm font-medium text-zinc-800">{scene.ai_role}</p>
          </div>
        </div>

        {/* Task goal */}
        <div className="border-b border-zinc-100 p-5">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-zinc-400">
            Task Goal
          </p>
          <p className="mt-1.5 text-xs leading-relaxed text-zinc-600">
            {scene.task_goal}
          </p>
        </div>

        {/* Must-cover */}
        {scene.must_cover_points && scene.must_cover_points.length > 0 && (
          <div className="border-b border-zinc-100 p-5">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-zinc-400">
              Must Cover
            </p>
            <ul className="mt-2 space-y-1.5">
              {scene.must_cover_points.map((pt, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-zinc-600">
                  <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-[10px] font-bold text-indigo-600">
                    {i + 1}
                  </span>
                  {pt}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Key expressions */}
        {scene.key_expressions && scene.key_expressions.length > 0 && (
          <div className="border-b border-zinc-100 p-5">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-zinc-400">
              Key Expressions
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {scene.key_expressions.map((expr, i) => (
                <span
                  key={i}
                  className="rounded-md border border-zinc-200 bg-zinc-50 px-2 py-1 text-[11px] text-zinc-600"
                >
                  {expr}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Latency panel */}
        <div className="p-5 space-y-3">
          <LiveLatencyPanel latency={latency} turnStatus={turnStatus} />
          {sttDegraded && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-[10px] text-amber-700 leading-relaxed">
              ⚠️ 语音识别服务暂时不可用，已切换至备用模式。文字输入不受影响。
            </div>
          )}
        </div>
      </aside>

      {/* ── Chat area ─────────────────────────────────────── */}
      <main className="flex flex-1 flex-col min-w-0">
        {/* Top bar */}
        <header className="flex items-center gap-3 border-b border-zinc-200 bg-white px-5 py-3">
          <button
            onClick={() => router.push("/scenes")}
            className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 lg:hidden"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div className="flex-1">
            <h1 className="text-sm font-bold text-zinc-900 lg:hidden">{scene.title}</h1>
            <div className="flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${isCompleted ? "bg-emerald-500" : "bg-amber-400 animate-pulse"}`} />
              <span className="text-xs text-zinc-500">
                {isCompleted ? "Session complete" : "Conversation active"}
              </span>
            </div>
          </div>
          {finishing ? (
            <span className="text-xs font-medium text-indigo-600 animate-pulse">
              Generating your speaking report…
            </span>
          ) : (
            <button
              onClick={handleEndSession}
              className="text-xs font-medium text-indigo-600 hover:text-indigo-800"
            >
              End Session
            </button>
          )}
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="mx-auto max-w-2xl space-y-4">
            {turns.length === 0 && (
              <p className="text-center text-sm text-zinc-400 py-20">
                Start the conversation by typing below.
              </p>
            )}

            {turns.map((turn) => {
              const isUser = turn.role === "user";
              return (
                <div
                  key={turn.id}
                  className={`flex ${isUser ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                      isUser
                        ? "bg-indigo-600 text-white rounded-br-md"
                        : "bg-white border border-zinc-200 text-zinc-800 rounded-bl-md"
                    }`}
                  >
                    <p>{turn.message}</p>
                    {/* AI metadata */}
                    {!isUser && turn.intent && turn.intent !== "open_conversation" && (
                      <div className="mt-2 flex flex-wrap gap-1.5 border-t border-zinc-100 pt-2">
                        {turn.intent && (
                          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] text-zinc-500">
                            intent: {turn.intent}
                          </span>
                        )}
                        {turn.next_goal && turn.next_goal !== "end" && (
                          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] text-zinc-500">
                            next: {turn.next_goal}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {/* Typing indicator */}
            {sending && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-2xl rounded-bl-md border border-zinc-200 bg-white px-4 py-3 shadow-sm">
                  <div className="flex items-center gap-1.5">
                    <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-400" style={{ animationDelay: "0ms" }} />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-400" style={{ animationDelay: "150ms" }} />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-400" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>
        </div>

        {/* Correction hints */}
        {(latestHints.length > 0 || latestScores) && (
          <div className="mx-5 mb-2">
            <CorrectionHintPanel hints={latestHints} scores={latestScores} pronunciation={latestPron} />
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div className="mx-5 mb-2 rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-xs text-red-700">
            {error}
            <button onClick={() => setError(null)} className="ml-2 underline">Dismiss</button>
          </div>
        )}

        {/* Input bar — Speak or type */}
        <div className="border-t border-zinc-200 bg-white px-4 py-3">
          <p className="text-center text-xs font-medium text-zinc-400 mb-2">Speak or type your answer</p>
          <div className="mx-auto max-w-2xl space-y-3">
            {/* Text input */}
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKey}
                disabled={sending || isCompleted}
                placeholder={isCompleted ? "Session complete" : "Type your reply…"}
                className="flex-1 rounded-xl border border-zinc-300 bg-white px-4 py-3 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 disabled:bg-zinc-50 disabled:text-zinc-400"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || sending || isCompleted}
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>

            {/* Divider */}
            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-zinc-200" />
              <span className="text-xs text-zinc-400 font-medium">or</span>
              <div className="flex-1 h-px bg-zinc-200" />
            </div>

            {/* Voice recorder */}
            <div className="flex justify-center">
              <VoiceRecorder
                onRecordingComplete={handleVoiceRecording}
                disabled={sending || isCompleted}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

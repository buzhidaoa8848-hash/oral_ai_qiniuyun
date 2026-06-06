"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import type { SessionReport, ConversationTurn } from "@/lib/types";
import { fetchSessionReport, finishSession, fetchTurns } from "@/lib/api";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

function ScoreRing({ score, label }: { score: number; label: string }) {
  const pct = Math.min(100, Math.max(0, score));
  const color =
    pct >= 85 ? "text-emerald-600 stroke-emerald-500" :
    pct >= 65 ? "text-amber-600 stroke-amber-500" :
    "text-red-600 stroke-red-500";
  const circumference = 2 * Math.PI * 38;
  const offset = circumference - (pct / 100) * circumference;
  return (
    <div className="flex flex-col items-center">
      <svg className="h-24 w-24" viewBox="0 0 96 96">
        <circle cx="48" cy="48" r="38" fill="none" className="stroke-zinc-100" strokeWidth="6" />
        <circle
          cx="48" cy="48" r="38" fill="none" strokeWidth="6" strokeLinecap="round"
          className={color} strokeDasharray={circumference} strokeDashoffset={offset}
          transform="rotate(-90 48 48)" style={{ transition: "stroke-dashoffset 1s ease" }}
        />
        <text x="48" y="48" textAnchor="middle" dominantBaseline="central"
          className={`text-lg font-bold ${color}`}>{Math.round(pct)}</text>
      </svg>
      <span className="mt-1 text-xs font-medium text-zinc-500">{label}</span>
    </div>
  );
}

function SmallCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-zinc-700 mb-3">{title}</h3>
      {children}
    </div>
  );
}

export default function ReportPage() {
  const params = useParams<{ sessionId: string }>();
  const router = useRouter();
  const [report, setReport] = useState<SessionReport | null>(null);
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params?.sessionId) return;
    (async () => {
      try {
        // Auto-finish the session first
        await finishSession(params.sessionId).catch(() => {});
        const [r, t] = await Promise.all([
          fetchSessionReport(params.sessionId),
          fetchTurns(params.sessionId),
        ]);
        setReport(r);
        setTurns(t);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load report");
      } finally {
        setLoading(false);
      }
    })();
  }, [params?.sessionId]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-zinc-200 border-t-indigo-600" />
          <p className="mt-4 text-sm text-zinc-500">Generating report…</p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50">
        <div className="text-center">
          <p className="text-red-600">{error ?? "Report not found"}</p>
          <button onClick={() => router.push("/scenes")} className="mt-3 text-sm text-indigo-600 hover:underline">
            Back to scenes
          </button>
        </div>
      </div>
    );
  }

  const radarData = [
    { dimension: "Grammar", score: report.grammar, fullMark: 100 },
    { dimension: "Expression", score: report.expression, fullMark: 100 },
    { dimension: "Naturalness", score: report.naturalness, fullMark: 100 },
    { dimension: "Task", score: report.task_completion, fullMark: 100 },
    ...(report.pronunciation > 0 || report.fluency > 0
      ? [
          { dimension: "Pron.", score: report.pronunciation, fullMark: 100 },
          { dimension: "Fluency", score: report.fluency, fullMark: 100 },
        ]
      : []),
  ];

  const hasVoiceData = report.pronunciation > 0 || report.fluency > 0;

  const timing = report.correction_timing_summary ?? {};
  const lat = report.latency_summary ?? {};
  const plan = report.next_practice_plan;

  return (
    <main className="min-h-screen bg-zinc-50 pb-16">
      {/* Header */}
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900">Session Report</h1>
            <p className="mt-1 text-sm text-zinc-500">
              {report.scene_title} · {report.turn_count} turns
            </p>
          </div>
          <button onClick={() => router.push("/scenes")} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
            Practice Again →
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-6 py-8 space-y-8">
        {/* ── Overall score ───────────────────────────────── */}
        <div className="flex flex-wrap items-center justify-center gap-8 rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm">
          <ScoreRing score={report.overall_score} label="Overall" />
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {([
              ["Grammar", report.grammar, true],
              ["Expression", report.expression, true],
              ["Naturalness", report.naturalness, true],
              ["Task", report.task_completion, true],
              ["Pronunciation", report.pronunciation, hasVoiceData],
              ["Fluency", report.fluency, hasVoiceData],
              ["Self-expr", report.self_expression, true],
            ] as const).map(([l, s, hasData]) => (
              <div key={l} className="flex flex-col items-center">
                {!hasData ? (
                  <>
                    <span className="text-xs text-zinc-400 italic font-medium">N/A</span>
                    <span className="text-[8px] text-zinc-300 text-center leading-tight mt-0.5">Voice mode<br />only</span>
                  </>
                ) : (
                  <>
                    <span className={`text-lg font-bold ${Number(s) >= 85 ? "text-emerald-600" : Number(s) >= 65 ? "text-amber-600" : "text-red-600"}`}>
                      {Math.round(Number(s))}
                    </span>
                    <span className="text-[10px] text-zinc-400">{l}</span>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* ── Voice data notice ──────────────────────────── */}
        {!hasVoiceData && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-5 py-3 text-sm text-amber-700 flex items-start gap-2.5">
            <span className="text-lg shrink-0">🎤</span>
            <div>
              <p className="font-semibold">发音与流利度评估不可用</p>
              <p className="text-xs text-amber-600 mt-0.5">
                本次练习使用文字模式，未录制语音。使用语音模式可获得发音评分、流利度分析和音素级反馈。
              </p>
            </div>
          </div>
        )}

        {/* ── Radar chart ──────────────────────────────────── */}
        <SmallCard title="Evaluation Radar">
          <div className="h-72">
            <ResponsiveContainer>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#e4e4e7" />
                <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 12, fill: "#71717a" }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10, fill: "#a1a1aa" }} />
                <Tooltip />
                <Radar name="Score" dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </SmallCard>

        <div className="grid gap-6 sm:grid-cols-2">
          {/* ── Correction timing ──────────────────────────── */}
          <SmallCard title="Correction Timing">
            {timing.total > 0 ? (
              <div className="space-y-2">
                {[
                  ["During session", (timing.light_recast ?? 0) + (timing.clarification ?? 0) + (timing.scaffold ?? 0)],
                  ["Post-session", timing.post_session ?? 0],
                  ["Immediate", timing.immediate_allowed ?? 0],
                ].map(([l, c]) => (
                  <div key={l} className="flex items-center justify-between text-sm">
                    <span className="text-zinc-600">{l}</span>
                    <span className="font-mono font-medium text-zinc-800">{c}</span>
                  </div>
                ))}
                <div className="border-t border-zinc-100 pt-2 flex justify-between text-sm font-semibold">
                  <span>Total</span>
                  <span>{timing.total}</span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-zinc-400">No corrections recorded — great job!</p>
            )}
          </SmallCard>

          {/* ── Latency ────────────────────────────────────── */}
          <SmallCard title="Latency Summary">
            {Object.keys(lat).filter(k => k !== "total_metrics" && k !== "e2e_estimate_ms").length > 0 ? (
              <div className="space-y-2">
                {Object.entries(lat)
                  .filter(([k]) => k !== "total_metrics" && k !== "e2e_estimate_ms")
                  .map(([cap, v]: [string, any]) => (
                    <div key={cap} className="flex items-center justify-between text-sm">
                      <span className="text-zinc-600 uppercase text-xs font-medium">{cap}</span>
                      <span className="font-mono text-zinc-800">
                        {v.avg_ms}ms <span className="text-zinc-400">({v.count}×)</span>
                      </span>
                    </div>
                  ))}
                {typeof lat.e2e_estimate_ms === "number" && (lat.e2e_estimate_ms as number) > 0 && (
                  <div className="border-t border-zinc-100 pt-2 flex justify-between text-sm font-semibold">
                    <span>Est. E2E</span>
                    <span>{String(lat.e2e_estimate_ms)}ms</span>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-zinc-400">No latency data for this session.</p>
            )}
          </SmallCard>

          {/* ── Top issues ─────────────────────────────────── */}
          <SmallCard title="Top Issues">
            {report.top_issues.length > 0 ? (
              <ul className="space-y-2">
                {report.top_issues.map((iss, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${
                      iss.severity >= 0.6 ? "bg-red-400" : iss.severity >= 0.3 ? "bg-amber-400" : "bg-zinc-300"
                    }`} />
                    <div>
                      <span className="text-zinc-700">{iss.error_text}</span>
                      <span className="ml-1.5 text-xs text-zinc-400">
                        ({iss.count}× · {iss.category} · {iss.timing})
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-zinc-400">No issues to highlight — keep it up!</p>
            )}
          </SmallCard>

          {/* ── Personal expression ────────────────────────── */}
          <SmallCard title="Personal Expression">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-zinc-500">Self-expression score</span>
                <span className="font-mono font-semibold">{Math.round(report.self_expression)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Turns</span>
                <span className="font-mono">{report.turn_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Scene</span>
                <span className="text-zinc-700">{report.scene_title}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Type</span>
                <span className="text-zinc-700 capitalize">{report.scene_type}</span>
              </div>
            </div>
          </SmallCard>
        </div>

        {/* ── If I were you ────────────────────────────────── */}
        <SmallCard title="If I Were You">
          <div className="rounded-lg border border-indigo-100 bg-indigo-50/50 p-4">
            <p className="text-sm leading-relaxed text-indigo-900 italic">
              &ldquo;{report.if_i_were_you}&rdquo;
            </p>
          </div>
        </SmallCard>

        {/* ── Next practice plan ───────────────────────────── */}
        {plan && (
          <SmallCard title="Next Practice Plan">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-3">
                <p className="text-xs text-zinc-400 uppercase font-semibold">Weakest Area</p>
                <p className="text-base font-semibold text-zinc-800 capitalize">{plan.weakest_area}</p>
                <p className="text-sm text-zinc-500">Score: {Math.round(plan.weakest_score)}</p>
              </div>
              <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-3">
                <p className="text-xs text-zinc-400 uppercase font-semibold">Suggested Scene</p>
                <p className="text-sm text-zinc-700">{plan.suggested_scene}</p>
              </div>
            </div>
            {plan.expression_goal && (
              <p className="mt-3 text-sm text-zinc-500">
                🎯 Your goal: <span className="font-medium text-zinc-700">{plan.expression_goal}</span>
              </p>
            )}
            <p className="mt-2 text-xs text-zinc-400 italic">{plan.tip}</p>
          </SmallCard>
        )}

        {/* ── Conversation Replay ────────────────────────── */}
        {turns.length > 0 && (
          <SmallCard title="Conversation Replay">
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {turns.map((turn) => {
                const isUser = turn.role === "user";
                return (
                  <div key={turn.id} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-[75%] rounded-xl px-4 py-2.5 text-sm ${
                        isUser
                          ? "bg-indigo-50 border border-indigo-100 text-indigo-900"
                          : "bg-zinc-50 border border-zinc-200 text-zinc-700"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-semibold text-zinc-400 uppercase">
                          {isUser ? "You" : "AI"}
                        </span>
                        {!isUser && turn.intent && turn.intent !== "open_conversation" && (
                          <span className="text-[9px] text-zinc-400 bg-zinc-100 rounded px-1.5 py-0.5">
                            {turn.intent}
                          </span>
                        )}
                      </div>
                      <p className="leading-relaxed whitespace-pre-wrap">{turn.message}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </SmallCard>
        )}
      </div>
    </main>
  );
}

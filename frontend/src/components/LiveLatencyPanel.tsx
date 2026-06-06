"use client";

import type { LatencySnapshot } from "@/lib/types";

interface LiveLatencyPanelProps {
  latency: LatencySnapshot | null;
  turnStatus: "idle" | "recording" | "transcribing" | "llm" | "tts" | "complete";
}

const BAR_MAX_MS = 3000; // 3 seconds as max for the visual bar

function LatencyBar({ label, ms, color }: { label: string; ms: number; color: string }) {
  const pct = Math.min((ms / BAR_MAX_MS) * 100, 100);
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-8 shrink-0 font-medium text-zinc-500">{label}</span>
      <div className="flex-1 h-2 bg-zinc-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-12 shrink-0 text-right tabular-nums text-zinc-600">
        {ms > 0 ? `${ms}ms` : "—"}
      </span>
    </div>
  );
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  idle: { label: "Waiting", color: "bg-zinc-300" },
  recording: { label: "Recording", color: "bg-red-400" },
  transcribing: { label: "Transcribing", color: "bg-amber-400" },
  llm: { label: "AI Thinking", color: "bg-indigo-400" },
  tts: { label: "Speaking", color: "bg-emerald-400" },
  complete: { label: "Done", color: "bg-emerald-500" },
};

export default function LiveLatencyPanel({ latency, turnStatus }: LiveLatencyPanelProps) {
  const statusInfo = STATUS_LABELS[turnStatus] ?? STATUS_LABELS.idle;

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
      {/* Status indicator */}
      <div className="mb-3 flex items-center gap-2">
        <span
          className={`h-2.5 w-2.5 rounded-full ${
            turnStatus === "complete" ? "bg-emerald-500" : "animate-pulse " + statusInfo.color
          }`}
        />
        <span className="text-xs font-semibold text-zinc-600">
          {statusInfo.label}
        </span>
        {latency && (
          <span className="ml-auto text-xs font-mono tabular-nums text-zinc-400">
            E2E: {latency.e2e_ms}ms
          </span>
        )}
      </div>

      {/* Latency bars */}
      <div className="space-y-2">
        <LatencyBar
          label="STT"
          ms={latency?.stt_ms ?? 0}
          color="bg-amber-400"
        />
        <LatencyBar
          label="LLM"
          ms={latency?.llm_ms ?? 0}
          color="bg-indigo-400"
        />
        <LatencyBar
          label="TTS"
          ms={latency?.tts_ms ?? 0}
          color="bg-emerald-400"
        />
      </div>

      {/* History summary */}
      {latency && latency.e2e_ms > 0 && (
        <div className="mt-3 border-t border-zinc-100 pt-3 flex justify-between text-[10px] text-zinc-400">
          <span>
            STT {Math.round((latency.stt_ms / latency.e2e_ms) * 100)}%
          </span>
          <span>
            LLM {Math.round((latency.llm_ms / latency.e2e_ms) * 100)}%
          </span>
          <span>
            TTS {Math.round((latency.tts_ms / latency.e2e_ms) * 100)}%
          </span>
        </div>
      )}
    </div>
  );
}

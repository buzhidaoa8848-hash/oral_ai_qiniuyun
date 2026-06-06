"use client";

import type { PronunciationResult } from "@/lib/types";

interface CorrectionHintPanelProps {
  hints: string[];
  scores: {
    grammar: { score: number; notes: string };
    expression: { score: number; notes: string };
    naturalness: { score: number; notes: string };
    task_completion: { score: number; notes: string };
  } | null;
  pronunciation?: PronunciationResult | null;
}

function ScoreBadge({ label, score }: { label: string; score: number }) {
  const color =
    score >= 90 ? "bg-emerald-100 text-emerald-700" :
    score >= 70 ? "bg-amber-100 text-amber-700" :
    "bg-red-100 text-red-700";
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${color}`}>
      {label} {score}
    </span>
  );
}

export default function CorrectionHintPanel({ hints, scores, pronunciation }: CorrectionHintPanelProps) {
  if ((!hints || hints.length === 0) && !scores && !pronunciation) return null;

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50/60 p-4 shadow-sm">
      {/* Score badges */}
      {scores && (
        <div className="mb-3 flex flex-wrap gap-1.5">
          <ScoreBadge label="Grammar" score={scores.grammar.score} />
          <ScoreBadge label="Expression" score={scores.expression.score} />
          <ScoreBadge label="Natural" score={scores.naturalness.score} />
          <ScoreBadge label="Task" score={scores.task_completion.score} />
          {pronunciation && (
            <>
              <ScoreBadge label="Pron" score={pronunciation.pronunciation_score} />
              <ScoreBadge label="Fluency" score={pronunciation.fluency_score} />
            </>
          )}
        </div>
      )}

      {/* Pronunciation details */}
      {pronunciation && (
        <div className="mb-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] text-zinc-500">
          <span>WPM: {pronunciation.words_per_minute}</span>
          <span>·</span>
          <span>Fillers: {pronunciation.filler_word_count}</span>
          <span>·</span>
          <span>Words: {pronunciation.transcript_length}</span>
          {pronunciation.is_estimated && (
            <span className="rounded bg-zinc-100 px-1.5 py-0.5 text-[9px] text-zinc-400 italic">
              estimated from transcript and audio duration
            </span>
          )}
        </div>
      )}

      {/* Light hints */}
      {hints.length > 0 && (
        <div className="space-y-1.5">
          {hints.map((hint, i) => (
            <div key={i} className="flex items-start gap-1.5 text-xs text-amber-800">
              <span className="mt-0.5 shrink-0 text-amber-500">•</span>
              <span>{hint}</span>
            </div>
          ))}
        </div>
      )}

      {/* Phoneme feedback from pronunciation */}
      {pronunciation?.phoneme_feedback && (
        <p className="mt-2 text-[10px] text-amber-500 italic">
          {pronunciation.phoneme_feedback}
        </p>
      )}

      {/* Footer */}
      {hints.length > 0 && (
        <p className="mt-2 text-[10px] text-amber-400">
          Detailed feedback saved for your session report.
        </p>
      )}
    </div>
  );
}

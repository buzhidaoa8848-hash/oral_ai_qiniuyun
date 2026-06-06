// ═══════════════════════════════════════════════════════════════
// Mirror of backend Pydantic schemas — SceneCard, PracticeSession
// ═══════════════════════════════════════════════════════════════

export interface SceneCard {
  id: string;
  title: string;
  difficulty: string;
  topic: string;
  scene_type: string;
  style: string;
  ai_role: string;
  user_role: string;
  task_goal: string;
  key_expressions: string[] | null;
  must_cover_points: string[] | null;
  follow_up_strategy: string;
  evaluation_rubric: string;
  opening_question: string;
  prompt: string;
  character_role: string;
  model_answer: string;
  hints: string[] | null;
  target_language: string;
  source_language: string;
  tags: string[] | null;
  material_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationTurn {
  id: string;
  session_id: string;
  turn_index: number;
  role: string; // "user" | "ai"
  message: string;
  intent: string | null;
  based_on_user_point: string | null;
  next_goal: string | null;
  should_interrupt: boolean;
  audio_url: string | null;
  transcript: string | null;
  created_at: string;
}

export interface PronunciationResult {
  words_per_minute: number;
  filler_word_count: number;
  repeated_word_count: number;
  transcript_length: number;
  audio_duration_seconds: number;
  fluency_score: number;
  pronunciation_score: number;
  phoneme_feedback: string | null;
  provider_name: string;
  is_estimated: boolean;
}

export interface LatencySnapshot {
  stt_ms: number;
  pron_ms: number;
  llm_ms: number;
  tts_ms: number;
  e2e_ms: number;
}

export interface VoiceTurnResponse {
  transcript: string;
  reply: string;
  intent: string;
  based_on_user_point: string;
  next_goal: string;
  should_interrupt: boolean;
  is_final: boolean;
  user_turn: ConversationTurn;
  ai_turn: ConversationTurn;
  latency: LatencySnapshot;
  pronunciation: PronunciationResult;
  stt_degraded?: boolean;
  light_hints: string[];
  evaluation: EvaluationScores | null;
}

export interface EvaluationScores {
  grammar: { score: number; notes: string };
  expression: { score: number; notes: string };
  naturalness: { score: number; notes: string };
  task_completion: { score: number; notes: string };
}

export interface ConversationResponse {
  reply: string;
  intent: string;
  based_on_user_point: string;
  next_goal: string;
  should_interrupt: boolean;
  is_final: boolean;
  user_turn: ConversationTurn;
  ai_turn: ConversationTurn;
  light_hints: string[];
  evaluation: EvaluationScores | null;
}

export interface PracticeSession {
  id: string;
  profile_id: string;
  scene_card_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Profile {
  id: string;
  name: string;
  email: string | null;
  source_language: string;
  target_language: string;
  proficiency_level: string;
  identity: string | null;
  experiences: string | null;
  strengths: string | null;
  thinking_style: string | null;
  target_role: string | null;
  expression_goal: string | null;
  learner_identity: string | null;
  cefr_level: string | null;
  ielts_score: number | null;
  toefl_score: number | null;
  cet4_score: number | null;
  cet6_score: number | null;
  gaokao_english_score: number | null;
  zhongkao_english_score: number | null;
  created_at: string;
  updated_at: string;
}

export interface Material {
  id: string;
  title: string;
  content: string;
  material_type: string;
  language: string;
  raw_text: string;
  source_type: string;
  metadata_json: string | null;
  created_at: string;
  updated_at: string;
}

export interface SceneGenerateRequest {
  scene_type: string;
  style: string;
  user_level: string;
  target_goal: string;
}

export interface SceneGenerateResponse {
  scene_card_id: string;
  scene: SceneCard;
}

export interface SessionReport {
  session_id: string;
  status: string;
  scene_title: string;
  scene_type: string;
  turn_count: number;
  started_at: string | null;
  completed_at: string | null;
  overall_score: number;
  pronunciation: number;
  fluency: number;
  grammar: number;
  expression: number;
  task_completion: number;
  self_expression: number;
  naturalness: number;
  latency_summary: Record<string, { avg_ms: number; min_ms: number; max_ms: number; count: number } | number> & { total_metrics?: number; e2e_estimate_ms?: number };
  correction_timing_summary: Record<string, number>;
  top_issues: Array<{ error_text: string; correction: string; category: string; count: number; timing: string; severity: number }>;
  if_i_were_you: string;
  next_practice_plan: { weakest_area: string; weakest_score: number; suggested_scene: string; tip: string; expression_goal: string | null };
}

/** Difficulty badge colour map */
export const DIFFICULTY_COLORS: Record<string, string> = {
  A1: "bg-emerald-100 text-emerald-800",
  A2: "bg-green-100 text-green-800",
  B1: "bg-blue-100 text-blue-800",
  B2: "bg-indigo-100 text-indigo-800",
  C1: "bg-purple-100 text-purple-800",
  C2: "bg-rose-100 text-rose-800",
};

/** Scene type icon map (emoji fallback) */
export const SCENE_TYPE_ICONS: Record<string, string> = {
  interview: "💼",
  restaurant: "🍽️",
  meeting: "📊",
  pitch: "🚀",
  conversation: "💬",
};

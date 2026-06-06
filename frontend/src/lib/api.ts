// ═══════════════════════════════════════════════════════════════
// Thin API client for the SceneTalk backend.
// All requests go to NEXT_PUBLIC_API_URL (defaults to localhost:8000).
// ═══════════════════════════════════════════════════════════════

import type {
  SceneCard,
  PracticeSession,
  Profile,
  Material,
  ConversationTurn,
  ConversationResponse,
  VoiceTurnResponse,
  LatencySnapshot,
  SessionReport,
  SceneGenerateRequest,
  SceneGenerateResponse,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Wrap fetch with network-error handling.
 * Browser fetch() throws "Failed to fetch" on CORS blocks, connection
 * refused, or DNS failures — none of which tell the user what to do.
 * This wrapper turns those into actionable Chinese messages.
 */
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...options?.headers },
      ...options,
    });
  } catch (_e: unknown) {
    throw new Error(
      `无法连接后端服务 (${BASE})。请确保：\n1. 后端已启动: cd backend && uvicorn app.main:app --reload\n2. 防火墙未阻止端口 ${new URL(BASE).port || "8000"}`
    );
  }
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail ?? `请求失败 (HTTP ${res.status})`);
  }
  if (res.status === 204) return undefined as unknown as T;
  return res.json();
}

// ── Scenes ─────────────────────────────────────────────────────

export function fetchScenes(): Promise<SceneCard[]> {
  return request<SceneCard[]>("/api/scenes");
}

export function fetchScene(id: string): Promise<SceneCard> {
  return request<SceneCard>(`/api/scenes/${id}`);
}

// ── Sessions ───────────────────────────────────────────────────

export function createSession(
  profileId: string,
  sceneCardId: string
): Promise<PracticeSession> {
  return request<PracticeSession>("/api/sessions", {
    method: "POST",
    body: JSON.stringify({
      profile_id: profileId,
      scene_card_id: sceneCardId,
    }),
  });
}

export function fetchSession(id: string): Promise<PracticeSession> {
  return request<PracticeSession>(`/api/sessions/${id}`);
}

export function fetchTurns(sessionId: string): Promise<ConversationTurn[]> {
  return request<ConversationTurn[]>(`/api/sessions/${sessionId}/turns`);
}

export function postTurn(
  sessionId: string,
  message: string
): Promise<ConversationResponse> {
  return request<ConversationResponse>(`/api/sessions/${sessionId}/turns`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

// ── Materials ──────────────────────────────────────────────────

export function fetchMaterials(): Promise<Material[]> {
  return request<Material[]>("/api/materials");
}

export function fetchMaterial(id: string): Promise<Material> {
  return request<Material>(`/api/materials/${id}`);
}

export function createMaterialFromPaste(data: {
  title: string;
  raw_text: string;
  source_type?: string;
  language?: string;
}): Promise<Material> {
  return request<Material>("/api/materials", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function uploadMaterialFile(file: File): Promise<Material> {
  const formData = new FormData();
  formData.append("file", file);
  return fetch(`${BASE}/api/materials/upload`, {
    method: "POST",
    body: formData,
  }).then((res) => {
    if (!res.ok) throw new Error("Upload failed");
    return res.json();
  });
}

export function generateScene(
  materialId: string,
  req: SceneGenerateRequest
): Promise<SceneGenerateResponse> {
  return request<SceneGenerateResponse>(
    `/api/materials/${materialId}/generate-scene`,
    {
      method: "POST",
      body: JSON.stringify(req),
    }
  );
}

// ── Profiles ───────────────────────────────────────────────────

export function fetchProfiles(): Promise<Profile[]> {
  return request<Profile[]>("/api/profiles");
}

export function createProfile(name: string): Promise<Profile> {
  return request<Profile>("/api/profiles", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export function updateProfile(
  id: string,
  data: Partial<Profile>
): Promise<Profile> {
  return request<Profile>(`/api/profiles/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

// ── Voice ──────────────────────────────────────────────────────

export async function voiceTurn(
  sessionId: string,
  audioBlob: Blob
): Promise<VoiceTurnResponse> {
  const formData = new FormData();
  formData.append("file", audioBlob, "recording.webm");
  const res = await fetch(`${BASE}/api/voice/sessions/${sessionId}/voice-turn`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({} as Record<string, unknown>));
    const serverMsg = (body.message ?? body.detail ?? "") as string;
    // STT / upstream failure
    if (res.status === 502 || (serverMsg && /STT|LLM|DashScope|transcrib/i.test(serverMsg))) {
      throw new Error(serverMsg || "语音识别失败，请重试，或使用文字输入继续练习。");
    }
    // Empty or too-short audio
    if (res.status === 400) {
      throw new Error(serverMsg || "录音太短或为空，请至少录制 1 秒后重试。");
    }
    // Backend down / network error → message fallback
    if (res.status >= 500) {
      throw new Error(serverMsg || "后端服务暂时不可用，请稍后重试或使用文字输入继续练习。");
    }
    throw new Error(serverMsg || `语音处理失败 (${res.status})，请重试。`);
  }
  return res.json();
}

// ── Reports ───────────────────────────────────────────────────

export function fetchSessionReport(
  sessionId: string
): Promise<SessionReport> {
  return request<SessionReport>(`/api/reports/session/${sessionId}`);
}

export function finishSession(sessionId: string): Promise<PracticeSession> {
  return request<PracticeSession>(`/api/sessions/${sessionId}/finish`, {
    method: "POST",
  });
}

export function updateTtsLatency(
  sessionId: string,
  ttsMs: number
): Promise<void> {
  // We don't have a dedicated endpoint for this; store it locally.
  // The latency panel tracks TTS client-side.
  return Promise.resolve();
}

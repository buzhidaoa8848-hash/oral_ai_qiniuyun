"""Qwen / DashScope STT provider — Paraformer speech recognition.

API docs: https://help.aliyun.com/zh/model-studio/speech-recognition

Supported input formats (from docs): wav, pcm, mp3, speex, wma, ogg, amr, aac, opus, flac.
The frontend now converts browser MediaRecorder output (webm/opus) to WAV/PCM
before sending, so this provider expects to receive valid WAV data.
"""

from __future__ import annotations

import json
import logging
import os

import httpx

from .base import BaseSTTProvider

logger = logging.getLogger("scenetalk.stt.qwen")


class QwenSTTProvider(BaseSTTProvider):
    """DashScope Paraformer speech-to-text.

    Requires DASHSCOPE_API_KEY in env.
    """

    BASE_URL = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
        if not self.api_key:
            raise RuntimeError("DASHSCOPE_API_KEY 未设置，请在 .env 中配置或切换为 mock 模式")

        # Determine file extension from mime type
        ext = self._ext_from_mime(mime_type)
        filename = f"recording.{ext}"

        files = {"file": (filename, audio_bytes, mime_type)}

        # Use Paraformer v2 for best accuracy; fall back to paraformer-v1 if needed
        data = {"model": "paraformer-v2", "sample_rate": 16000}

        try:
            response = httpx.post(
                self.BASE_URL,
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )
        except httpx.TimeoutException:
            raise RuntimeError("DashScope STT 请求超时，请检查网络后重试")
        except httpx.ConnectError:
            raise RuntimeError("无法连接 DashScope 服务，请检查网络")
        except httpx.HTTPError as e:
            raise RuntimeError(f"DashScope STT 网络错误: {e}")

        # ── Handle non-200 responses with detailed logging ─────
        if not response.is_success:
            logger.error(
                "DashScope STT returned %s — body: %s",
                response.status_code,
                response.text[:500],
            )
            if response.status_code == 400:
                raise RuntimeError(
                    "语音识别请求格式错误。DashScope 期望 WAV/PCM 格式的音频。"
                    "如果此问题持续出现，请使用文字输入模式。"
                )
            elif response.status_code == 401:
                raise RuntimeError("DashScope API Key 无效，请检查 DASHSCOPE_API_KEY")
            elif response.status_code == 429:
                raise RuntimeError("DashScope API 调用频率超限，请稍后重试")
            else:
                raise RuntimeError(
                    f"语音识别服务异常 (HTTP {response.status_code})，请重试或使用文字输入"
                )

        # ── Parse response ─────────────────────────────────────
        try:
            result = response.json()
        except json.JSONDecodeError:
            logger.error("DashScope STT returned non-JSON: %s", response.text[:300])
            raise RuntimeError("语音识别返回数据异常，请重试")

        logger.debug("DashScope STT response: %s", json.dumps(result, ensure_ascii=False)[:300])

        # ── Extract text from various response shapes ──────────
        output = result.get("output", {})

        if "results" in output:
            # Newer API shape: list of segments
            texts = [r.get("text", "") for r in output["results"]]
            transcript = " ".join(texts).strip()
        elif "text" in output:
            transcript = output["text"]
        elif "sentence" in output:
            sent = output["sentence"]
            if isinstance(sent, list):
                texts = [s.get("text", "") for s in sent]
                transcript = "".join(texts).strip()
            else:
                transcript = str(sent)
        elif "transcript" in output:
            transcript = output["transcript"]
        else:
            logger.warning("DashScope STT: unrecognized response shape, keys=%s", list(output.keys()))
            transcript = str(output) if output else ""

        if not transcript.strip():
            logger.warning(
                "DashScope STT returned empty transcript. "
                "Raw output keys: %s",
                list(output.keys()),
            )
            raise RuntimeError(
                "语音识别未能识别到文字。请确保：\n"
                "1. 录音环境安静\n"
                "2. 麦克风未被占用\n"
                "3. 录音时长超过 1 秒\n"
                "如问题持续，请使用文字输入模式。"
            )

        return transcript.strip()

    @staticmethod
    def _ext_from_mime(mime: str) -> str:
        """Map MIME type to a file extension DashScope will accept."""
        mapping = {
            "audio/wav": "wav",
            "audio/wave": "wav",
            "audio/x-wav": "wav",
            "audio/pcm": "pcm",
            "audio/mpeg": "mp3",
            "audio/mp3": "mp3",
            "audio/mp4": "m4a",
            "audio/ogg": "ogg",
            "audio/webm": "webm",
            "audio/opus": "opus",
            "audio/aac": "aac",
            "audio/flac": "flac",
        }
        return mapping.get(mime, "wav")

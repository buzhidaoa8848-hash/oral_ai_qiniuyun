"""Test voice-turn endpoint error handling and edge cases."""

import io
import struct


def _make_wav(seconds: float = 1.0, sample_rate: int = 16000, loud: bool = True) -> bytes:
    """Create a minimal valid WAV file in memory.

    Args:
        seconds: duration in seconds
        sample_rate: sample rate in Hz
        loud: if True, fill with max-amplitude tone; if False, fill with silence
    """
    num_samples = int(sample_rate * seconds)
    data_size = num_samples * 2  # 16-bit mono

    buf = bytearray(44 + data_size)
    # RIFF header
    buf[0:4] = b"RIFF"
    struct.pack_into("<I", buf, 4, 36 + data_size)
    buf[8:12] = b"WAVE"
    # fmt chunk
    buf[12:16] = b"fmt "
    struct.pack_into("<I", buf, 16, 16)  # chunk size
    struct.pack_into("<H", buf, 20, 1)   # PCM
    struct.pack_into("<H", buf, 22, 1)   # mono
    struct.pack_into("<I", buf, 24, sample_rate)
    struct.pack_into("<I", buf, 28, sample_rate * 2)
    struct.pack_into("<H", buf, 32, 2)   # block align
    struct.pack_into("<H", buf, 34, 16)  # bits per sample
    # data chunk
    buf[36:40] = b"data"
    struct.pack_into("<I", buf, 40, data_size)

    # Fill samples
    for i in range(num_samples):
        offset = 44 + i * 2
        if loud:
            val = int(16000 * 1.0)  # max amplitude
        else:
            val = 0  # silence
        struct.pack_into("<h", buf, offset, val)

    return bytes(buf)


def _create_session(client):
    """Helper: create a profile and a session, return session_id."""
    # Get or create profile
    resp = client.get("/api/profiles")
    if resp.status_code == 200 and resp.json():
        profile_id = resp.json()[0]["id"]
    else:
        resp = client.post("/api/profiles", json={"name": "Test"})
        assert resp.status_code == 201
        profile_id = resp.json()["id"]

    # Use first scene card
    resp = client.get("/api/scenes")
    assert resp.status_code == 200
    scene_id = resp.json()[0]["id"]

    # Create session
    resp = client.post(
        "/api/sessions",
        json={"profile_id": profile_id, "scene_card_id": scene_id},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ── Tests ────────────────────────────────────────────────────────

def test_voice_turn_session_not_found(client):
    """Non-existent session should return 404."""
    wav = _make_wav(seconds=1.0, loud=True)
    resp = client.post(
        "/api/voice/sessions/00000000-0000-0000-0000-000000000000/voice-turn",
        files={"file": ("test.wav", io.BytesIO(wav), "audio/wav")},
    )
    assert resp.status_code == 404


def test_voice_turn_empty_audio(client):
    """Audio shorter than 500 bytes should return 400."""
    session_id = _create_session(client)
    # Send a very tiny "audio" file
    tiny = b"\x00" * 100
    resp = client.post(
        f"/api/voice/sessions/{session_id}/voice-turn",
        files={"file": ("tiny.wav", io.BytesIO(tiny), "audio/wav")},
    )
    assert resp.status_code == 400
    detail = resp.json().get("detail", "")
    assert "太短" in detail or "empty" in detail.lower()


def test_voice_turn_silent_audio(client):
    """Silent WAV audio should return 400 with a helpful message."""
    session_id = _create_session(client)
    wav = _make_wav(seconds=1.0, loud=False)  # all zeros
    resp = client.post(
        f"/api/voice/sessions/{session_id}/voice-turn",
        files={"file": ("silence.wav", io.BytesIO(wav), "audio/wav")},
    )
    assert resp.status_code == 400
    detail = resp.json().get("detail", "")
    assert "语音" in detail or "audio" in detail.lower()


def test_voice_turn_loud_audio_succeeds(client):
    """Loud WAV should succeed (mock STT returns a placeholder)."""
    session_id = _create_session(client)
    wav = _make_wav(seconds=1.0, loud=True)
    resp = client.post(
        f"/api/voice/sessions/{session_id}/voice-turn",
        files={"file": ("loud.wav", io.BytesIO(wav), "audio/wav")},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "transcript" in data
    assert "reply" in data
    assert "latency" in data
    assert data["latency"]["stt_ms"] >= 0
    # stt_degraded may be True in test env (no real STT key configured)


def test_voice_turn_webm_format(client):
    """webm audio (from MediaRecorder, before frontend WAV conversion) should be handled."""
    session_id = _create_session(client)
    # Create a noisy byte blob pretending to be webm (mock STT handles anything)
    webm = b"\x1a\x45\xdf\xa3" + b"\x00" * 2000  # webm EBML header
    resp = client.post(
        f"/api/voice/sessions/{session_id}/voice-turn",
        files={"file": ("recording.webm", io.BytesIO(webm), "audio/webm")},
    )
    # Mock mode should handle this gracefully
    assert resp.status_code in (200, 400), resp.text

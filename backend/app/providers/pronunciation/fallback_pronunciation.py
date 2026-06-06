"""Fallback pronunciation provider — estimates from transcript + audio duration.

Computes:
- words_per_minute (WPM)
- filler words (um, uh, like, you know, etc.)
- repeated words (same word ≥3 times in short text)
- fluency_score (0–100 from WPM + fillers + repetitions)
- pronunciation_score (approximate, from fluency + transcript length)

All metrics are ESTIMATES — not real acoustic analysis.
"""

from __future__ import annotations

from .base import BasePronunciationProvider, PronunciationResult

# ── Filler word set ───────────────────────────────────────────
_FILLERS = {
    "um", "uh", "er", "ah", "like", "you know", "i mean",
    "sort of", "kind of", "basically", "actually", "literally",
    "so yeah", "right", "okay so",
}

# Single-word fillers for quick matching
_FILLER_SINGLE = {"um", "uh", "er", "ah", "like"}


class FallbackPronunciationProvider(BasePronunciationProvider):

    def evaluate(
        self,
        audio_bytes: bytes,
        transcript: str,
        audio_duration_seconds: float,
    ) -> PronunciationResult:
        words = transcript.strip().split()
        word_count = len(words)

        # ── WPM ──────────────────────────────────────────────
        duration = max(audio_duration_seconds, 0.5)  # avoid div-by-zero
        wpm = (word_count / duration) * 60.0

        # ── Filler words ─────────────────────────────────────
        text_lower = transcript.lower()
        filler_count = 0
        filler_found: list[str] = []
        for fw in _FILLER_SINGLE:
            # Count as standalone words, not substrings
            count = sum(1 for w in words if w.lower().strip(".,!?") == fw)
            if count:
                filler_count += count
                filler_found.append(fw)
        # Multi-word fillers
        for fw in _FILLERS - _FILLER_SINGLE:
            count = text_lower.count(fw)
            if count:
                filler_count += count
                filler_found.append(fw)

        # ── Repeated words ───────────────────────────────────
        word_freq: dict[str, int] = {}
        for w in words:
            wl = w.lower().strip(".,!?;:'\"")
            if len(wl) > 3:
                word_freq[wl] = word_freq.get(wl, 0) + 1
        repeated = sum(c for c in word_freq.values() if c >= 3)
        repeated_count = repeated

        # ── Fluency score (0–100) ────────────────────────────
        # Penalize low WPM, high fillers, high repetitions
        wpm_score = min(100.0, max(0.0, wpm * 0.7))  # ~143 WPM = 100
        if wpm < 60:
            wpm_score = max(20.0, wpm * 1.2)          # very slow
        elif wpm > 200:
            wpm_score = max(40.0, 140 - (wpm - 200) * 0.3)  # too fast

        filler_penalty = min(40.0, filler_count * 8.0)
        repeat_penalty = min(20.0, repeated_count * 5.0)

        fluency = max(0.0, min(100.0, wpm_score - filler_penalty - repeat_penalty))

        # ── Pronunciation score (approximate) ────────────────
        # Based on fluency + transcript complexity
        # (Real implementation would use acoustic features)
        unique_ratio = len(set(w.lower() for w in words)) / max(word_count, 1)
        vocab_bonus = min(15.0, unique_ratio * 20.0)

        pronunciation = max(0.0, min(100.0, fluency * 0.75 + vocab_bonus))

        # ── Phoneme feedback ─────────────────────────────────
        notes: list[str] = []
        if filler_count > 3:
            notes.append(f"{filler_count} filler words ({', '.join(filler_found[:4])})")
        if repeated_count > 0:
            notes.append(f"{repeated_count} repeated word instances")
        if wpm < 80:
            notes.append(f"slow pace ({wpm:.0f} WPM)")
        elif wpm > 180:
            notes.append(f"fast pace ({wpm:.0f} WPM)")
        if word_count < 5:
            notes.append("very short response")

        phoneme_feedback = "; ".join(notes) if notes else None

        return PronunciationResult(
            words_per_minute=round(wpm, 1),
            filler_word_count=filler_count,
            repeated_word_count=repeated_count,
            transcript_length=word_count,
            audio_duration_seconds=round(duration, 2),
            fluency_score=round(fluency, 1),
            pronunciation_score=round(pronunciation, 1),
            phoneme_feedback=phoneme_feedback,
            provider_name="fallback",
            is_estimated=True,
        )

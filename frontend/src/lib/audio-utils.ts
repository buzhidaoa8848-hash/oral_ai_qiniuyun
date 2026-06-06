/**
 * Convert a MediaRecorder webm/opus Blob to 16kHz mono 16-bit PCM WAV.
 *
 * DashScope Paraformer (and most STT APIs) expect WAV/PCM, but the
 * browser MediaRecorder only outputs webm/opus.  This utility bridges
 * that gap using the Web Audio API — zero server-side dependencies.
 */

const TARGET_SAMPLE_RATE = 16000;

/**
 * Encode raw Float32 PCM samples as a 16-bit PCM WAV buffer.
 */
function encodeWav(samples: Float32Array, sampleRate: number): ArrayBuffer {
  const numChannels = 1; // mono
  const bitsPerSample = 16;
  const byteRate = sampleRate * numChannels * (bitsPerSample / 8);
  const blockAlign = numChannels * (bitsPerSample / 8);
  const dataSize = samples.length * (bitsPerSample / 8);
  const headerSize = 44;
  const buffer = new ArrayBuffer(headerSize + dataSize);
  const view = new DataView(buffer);

  // ── RIFF header ──────────────────────────────────────────
  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + dataSize, true); // file size - 8
  writeString(view, 8, "WAVE");

  // ── fmt  sub-chunk ───────────────────────────────────────
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true); // sub-chunk size (PCM)
  view.setUint16(20, 1, true); // audio format (1 = PCM)
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitsPerSample, true);

  // ── data sub-chunk ───────────────────────────────────────
  writeString(view, 36, "data");
  view.setUint32(40, dataSize, true);

  // Write 16-bit PCM samples (clamped)
  let offset = 44;
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    const int16 = s < 0 ? s * 0x8000 : s * 0x7fff;
    view.setInt16(offset, int16, true);
    offset += 2;
  }

  return buffer;
}

function writeString(view: DataView, offset: number, str: string): void {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i));
  }
}

/**
 * Convert an audio Blob (webm, ogg, mp4, etc.) to a 16kHz mono WAV Blob.
 *
 * Falls back to the original blob if Web Audio API is unavailable or
 * decoding fails (the backend will still try its best).
 */
export async function convertToWav(blob: Blob): Promise<Blob> {
  // ── Check Web Audio API availability ──────────────────────
  if (typeof AudioContext === "undefined" && typeof (window as any).webkitAudioContext === "undefined") {
    console.warn("Web Audio API not available — sending original audio format");
    return blob;
  }

  try {
    const arrayBuffer = await blob.arrayBuffer();
    const audioCtx = new (AudioContext || (window as any).webkitAudioContext)({ sampleRate: TARGET_SAMPLE_RATE });

    // Decode the source audio (webm/opus → raw PCM)
    const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);

    // Extract the first channel (mono)
    const channelData = audioBuffer.getChannelData(0);

    // Resample to target rate if needed
    let samples: Float32Array;
    if (audioBuffer.sampleRate !== TARGET_SAMPLE_RATE) {
      samples = resample(channelData, audioBuffer.sampleRate, TARGET_SAMPLE_RATE);
    } else {
      samples = channelData;
    }

    // Encode as WAV
    const wavBuffer = encodeWav(samples, TARGET_SAMPLE_RATE);

    await audioCtx.close();

    return new Blob([wavBuffer], { type: "audio/wav" });
  } catch (err) {
    console.warn("Audio conversion failed, sending original format:", err);
    return blob; // fallback: send original, server may still handle it
  }
}

/**
 * Simple linear resampling.
 */
function resample(
  input: Float32Array,
  inputRate: number,
  outputRate: number
): Float32Array {
  if (inputRate === outputRate) return input;
  const ratio = inputRate / outputRate;
  const outputLength = Math.round(input.length / ratio);
  const output = new Float32Array(outputLength);
  for (let i = 0; i < outputLength; i++) {
    const srcIndex = i * ratio;
    const srcFloor = Math.floor(srcIndex);
    const srcCeil = Math.min(srcFloor + 1, input.length - 1);
    const t = srcIndex - srcFloor;
    output[i] = input[srcFloor] * (1 - t) + input[srcCeil] * t;
  }
  return output;
}

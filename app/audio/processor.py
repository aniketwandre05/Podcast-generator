import io
import math
import wave
import numpy as np

def read_wav_bytes(wav_bytes: bytes):
    """Read in-memory WAV bytes into a numpy array and sample rate."""
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw_frames = wf.readframes(n_frames)

    dtype = np.int16 if sampwidth == 2 else (np.uint8 if sampwidth == 1 else np.int32)
    audio = np.frombuffer(raw_frames, dtype=dtype).astype(np.float32)

    # Convert to mono if multichannel
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)

    return audio, framerate

def write_wav_bytes(audio: np.ndarray, framerate: int = 22050) -> bytes:
    """Convert float32 numpy audio array back to 16-bit PCM WAV bytes."""
    # Clip to prevent overflow
    clipped = np.clip(audio, -32767.0, 32767.0).astype(np.int16)
    out_buf = io.BytesIO()
    with wave.open(out_buf, "wb") as wf:
        wf.setnchannels(1) # Mono
        wf.setsampwidth(2) # 16-bit
        wf.setframerate(framerate)
        wf.writeframes(clipped.tobytes())
    return out_buf.getvalue()

def trim_silence(audio: np.ndarray, threshold_db: float = -38.0, min_silence_samples: int = 400) -> np.ndarray:
    """Trim leading and trailing silence below threshold dB."""
    if len(audio) == 0:
        return audio

    max_val = np.max(np.abs(audio)) + 1e-6
    abs_audio = np.abs(audio) / max_val
    thresh = 10.0 ** (threshold_db / 20.0)

    is_loud = abs_audio > thresh
    indices = np.where(is_loud)[0]

    if len(indices) == 0:
        return audio

    start_idx = max(0, indices[0] - min_silence_samples)
    end_idx = min(len(audio), indices[-1] + min_silence_samples)
    return audio[start_idx:end_idx]

def normalize_loudness(audio: np.ndarray, target_peak: float = 0.90) -> np.ndarray:
    """Normalize peak audio to target level (default 90% full scale)."""
    if len(audio) == 0:
        return audio
    peak = np.max(np.abs(audio))
    if peak > 1e-4:
        scale = (32767.0 * target_peak) / peak
        return audio * scale
    return audio

def generate_silence(duration_ms: int, framerate: int = 22050) -> np.ndarray:
    """Generate numpy array of zeros representing silence for specified milliseconds."""
    samples = int((duration_ms / 1000.0) * framerate)
    return np.zeros(samples, dtype=np.float32)


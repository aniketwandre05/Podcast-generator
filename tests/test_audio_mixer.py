import numpy as np
import pytest
from app.audio.mixer import mix_podcast_episode
from app.audio.processor import (
    generate_silence,
    normalize_loudness,
    read_wav_bytes,
    trim_silence,
    write_wav_bytes,
)

def test_silence_generation():
    silence = generate_silence(500, framerate=22050)
    assert len(silence) == int(22050 * 0.5)
    assert np.all(silence == 0.0)

def test_wav_read_write_roundtrip():
    # 440 Hz test tone
    sr = 22050
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    orig = (np.sin(2 * np.pi * 440 * t) * 16000).astype(np.float32)

    wav_bytes = write_wav_bytes(orig, framerate=sr)
    assert len(wav_bytes) > 44

    loaded, loaded_sr = read_wav_bytes(wav_bytes)
    assert loaded_sr == sr
    assert len(loaded) == len(orig)
    # Check max difference within 1 unit due to 16-bit quant
    assert np.max(np.abs(orig - loaded)) <= 2.0

def test_loudness_normalization():
    quiet = np.array([100.0, -100.0, 50.0], dtype=np.float32)
    norm = normalize_loudness(quiet, target_peak=0.90)
    assert np.isclose(np.max(np.abs(norm)), 32767.0 * 0.90, atol=1.0)

def test_audio_mixer_stitching():
    sr = 22050
    t = np.linspace(0, 0.2, int(sr * 0.2), endpoint=False)
    tone1 = write_wav_bytes((np.sin(2 * np.pi * 440 * t) * 15000).astype(np.float32), sr)
    tone2 = write_wav_bytes((np.sin(2 * np.pi * 880 * t) * 15000).astype(np.float32), sr)

    turns = [
        ({"speaker": "HOST", "text": "Turn 1", "pause_after_ms": 200}, tone1),
        ({"speaker": "GUEST", "text": "Turn 2", "pause_after_ms": 300}, tone2),
    ]

    master_wav, timestamps, duration = mix_podcast_episode(
        turn_audio_bytes_list=turns,
        music_track_name="none",
        target_framerate=sr,
    )

    assert len(master_wav) > 1000
    assert len(timestamps) == 2
    assert duration > 0.5
    assert timestamps[0]["speaker"] == "HOST"
    assert timestamps[1]["speaker"] == "GUEST"


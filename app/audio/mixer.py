import os
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from app.audio.processor import (
    generate_silence,
    normalize_loudness,
    read_wav_bytes,
    trim_silence,
    write_wav_bytes,
)
from app.core.config import settings

def load_music_track(track_name: str, target_framerate: int = 22050) -> Optional[np.ndarray]:
    """Load background music track from assets/music/."""
    music_path = settings.MUSIC_DIR / track_name
    if not music_path.exists():
        return None
    try:
        with open(music_path, "rb") as f:
            audio, sr = read_wav_bytes(f.read())
        return audio
    except Exception:
        return None

def mix_podcast_episode(
    turn_audio_bytes_list: List[Tuple[Dict[str, Any], bytes]],
    music_track_name: Optional[str] = "chill_ambient.wav",
    music_volume: float = 0.10,
    target_framerate: int = 22050,
) -> Tuple[bytes, List[Dict[str, Any]], float]:
    """
    Stitch dialogue turns with natural pauses, track turn timestamps,
    and duck background music under the conversation.
    Returns: (master_wav_bytes, turn_timestamps, total_duration_seconds)
    """
    stitched_blocks = []
    turn_timestamps = []
    current_time_s = 0.5 # 500ms initial breather

    # 1. Lead-in silence
    stitched_blocks.append(generate_silence(500, target_framerate))

    for turn_info, wav_bytes in turn_audio_bytes_list:
        audio, sr = read_wav_bytes(wav_bytes)
        
        # Clean up chunk
        trimmed = trim_silence(audio)
        normalized = normalize_loudness(trimmed, target_peak=0.88)
        
        turn_duration_s = len(normalized) / float(target_framerate)
        start_time_s = current_time_s
        end_time_s = start_time_s + turn_duration_s
        
        turn_timestamps.append({
            "speaker": turn_info.get("speaker"),
            "text": turn_info.get("text"),
            "start": round(start_time_s, 2),
            "end": round(end_time_s, 2),
            "duration": round(turn_duration_s, 2),
        })

        stitched_blocks.append(normalized)
        current_time_s = end_time_s

        # Natural conversational pause
        pause_ms = turn_info.get("pause_after_ms", 350)
        # Cap pause between 150ms and 1500ms
        pause_ms = max(150, min(1500, pause_ms))
        stitched_blocks.append(generate_silence(pause_ms, target_framerate))
        current_time_s += pause_ms / 1000.0

    # 2. Outro tail silence (1 second)
    stitched_blocks.append(generate_silence(1000, target_framerate))
    current_time_s += 1.0

    voice_master = np.concatenate(stitched_blocks)
    total_samples = len(voice_master)
    total_duration = total_samples / float(target_framerate)

    # 3. Background Music Mixing & Ducking
    if music_track_name and music_track_name != "none":
        music_audio = load_music_track(music_track_name, target_framerate)
        if music_audio is not None and len(music_audio) > 0:
            # Loop music to cover the whole episode
            reps = int(np.ceil(total_samples / len(music_audio)))
            full_music = np.tile(music_audio, reps)[:total_samples]
            
            # Compute speech presence envelope (envelope smoothing)
            # Use downsampled envelope for ultra-fast convolution (1000x faster than full-rate convolution on cloud CPUs)
            downsample_factor = 50
            downsampled_voice = np.abs(voice_master[::downsample_factor])
            sub_kernel_size = max(3, int((target_framerate * 0.3) / downsample_factor))
            kernel = np.ones(sub_kernel_size, dtype=np.float32) / float(sub_kernel_size)
            sub_speech_env = np.convolve(downsampled_voice, kernel, mode="same")
            
            # Upsample back to match total_samples
            speech_env = np.repeat(sub_speech_env, downsample_factor)[:total_samples]
            if len(speech_env) < total_samples:
                speech_env = np.pad(speech_env, (0, total_samples - len(speech_env)), mode="edge")
            
            max_env = np.max(speech_env) + 1e-6
            speech_presence = np.clip(speech_env / (max_env * 0.2), 0.0, 1.0)
            
            # Ducking: when speech is present, music drops to 20% of its normal level
            duck_curve = 1.0 - (0.80 * speech_presence)
            
            # Intro fade-in (first 1.5s) & Outro fade-out (last 2s)
            fade_in_len = min(int(target_framerate * 1.5), total_samples)
            fade_out_len = min(int(target_framerate * 2.5), total_samples)
            
            fade_envelope = np.ones(total_samples, dtype=np.float32)
            fade_envelope[:fade_in_len] = np.linspace(0.0, 1.0, fade_in_len)
            fade_envelope[-fade_out_len:] = np.linspace(1.0, 0.0, fade_out_len)
            
            final_music = full_music * music_volume * duck_curve * fade_envelope
            
            # Mix voice + music
            master_mix = voice_master + final_music
            # Master normalization to avoid clipping
            master_mix = normalize_loudness(master_mix, target_peak=0.92)
        else:
            master_mix = voice_master
    else:
        master_mix = voice_master

    master_wav_bytes = write_wav_bytes(master_mix, target_framerate)
    return master_wav_bytes, turn_timestamps, total_duration


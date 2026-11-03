import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from app.audio.exporter import generate_show_notes_markdown, generate_srt
from app.audio.mixer import mix_podcast_episode
from app.core.config import settings
from app.core.database import init_db
from app.llm.script_generator import generate_episode_outline, generate_full_script
from app.models.schemas import Turn
from app.research.provider import summarize_and_build_brief
from app.sarvam.tts import synthesize_turn_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("podcastai.demo")

async def generate_demo_episode(language: str = "en-IN", output_name: str = "sample_english.wav"):
    """Generate a high-quality 1-minute 2-speaker sample podcast episode."""
    settings.validate_api_key()
    init_db()

    is_hindi = language.startswith("hi")
    
    if is_hindi:
        topic = "कृत्रिम बुद्धिमत्ता (AI) और भारतीय भाषाओं का भविष्य"
        speakers = [
            {"speaker_id": "HOST", "display_name": "Rohan", "voice": "rohan", "pace": 1.0, "language_code": "hi-IN"},
            {"speaker_id": "GUEST", "display_name": "Priya", "voice": "priya", "pace": 1.0, "language_code": "hi-IN"},
        ]
        sample_dialogue = [
            Turn(
                speaker="HOST",
                text="नमस्ते और पॉडकास्ट एआई में आपका स्वागत है! आज हम बात कर रहे हैं कि कैसे सर्वम एआई भारतीय भाषाओं को नई आवाज़ दे रहा है।",
                pause_after_ms=350,
                language_code="hi-IN",
            ),
            Turn(
                speaker="GUEST",
                text="बिल्कुल रोहन! बुलबुल और सर्वम के नए मॉडल्स से अब हिंदी और सभी भारतीय भाषाओं में नैचुरल बातचीत संभव हो गई है।",
                pause_after_ms=300,
                language_code="hi-IN",
            ),
            Turn(
                speaker="HOST",
                text="सच में प्रिया! चाहे पॉडकास्ट हो या कस्टमर सपोर्ट, यह तकनीक हर भारतीय के लिए एआई को आसान बना रही है।",
                pause_after_ms=400,
                language_code="hi-IN",
            ),
            Turn(
                speaker="GUEST",
                text="और सबसे अच्छी बात यह है कि इसकी आवाज़ बिल्कुल स्वाभाविक और इंसानी लगती है।",
                pause_after_ms=350,
                language_code="hi-IN",
            ),
            Turn(
                speaker="HOST",
                text="सुनने के लिए बहुत धन्यवाद! मिलते हैं अगले एपिसोड में, सिर्फ पॉडकास्ट एआई पर।",
                pause_after_ms=500,
                language_code="hi-IN",
            ),
        ]
        title = "पॉडकास्ट एआई: भारतीय भाषाओं में एआई क्रांति"
    else:
        topic = "The Rise of Voice AI and Indic Language Intelligence"
        speakers = [
            {"speaker_id": "HOST", "display_name": "Shubh", "voice": "shubh", "pace": 1.0, "language_code": "en-IN"},
            {"speaker_id": "GUEST", "display_name": "Priya", "voice": "priya", "pace": 1.0, "language_code": "en-IN"},
        ]
        sample_dialogue = [
            Turn(
                speaker="HOST",
                text="Welcome to PodcastAI! Today, we're diving into the future of conversational AI and natural speech synthesis powered by Sarvam AI.",
                pause_after_ms=350,
                language_code="en-IN",
            ),
            Turn(
                speaker="GUEST",
                text="Thanks for having me, Shubh! It's truly fascinating how Sarvam's Bulbul engine captures the genuine cadence and cultural nuances of Indian speakers.",
                pause_after_ms=300,
                language_code="en-IN",
            ),
            Turn(
                speaker="HOST",
                text="Right! Traditional TTS always felt a bit robotic, but here the dialogue flows naturally with expressive pauses and realistic interaction.",
                pause_after_ms=400,
                language_code="en-IN",
            ),
            Turn(
                speaker="GUEST",
                text="Exactly. And being able to generate complete multi-speaker episodes on demand opens up incredible possibilities for creators and educators alike.",
                pause_after_ms=350,
                language_code="en-IN",
            ),
            Turn(
                speaker="HOST",
                text="That's a wrap for this quick spotlight! Stay tuned for more cutting-edge audio innovations on PodcastAI.",
                pause_after_ms=500,
                language_code="en-IN",
            ),
        ]
        title = "The Voice Revolution: Sarvam AI & Next-Gen Audio"

    logger.info(f"Synthesizing {len(sample_dialogue)} turns for '{title}' ({language})...")

    turn_audio_list = []
    speaker_map = {s["speaker_id"]: s for s in speakers}

    for idx, turn in enumerate(sample_dialogue):
        sp = speaker_map[turn.speaker]
        logger.info(f"  [{idx+1}/{len(sample_dialogue)}] Synthesizing {turn.speaker} ({sp['voice']}): \"{turn.text[:40]}...\"")
        audio_chunks = await synthesize_turn_text(
            text=turn.text,
            voice=sp["voice"],
            language_code=turn.language_code,
            pace=sp["pace"],
            model="bulbul:v3",
        )
        turn_wav = audio_chunks[0]
        turn_audio_list.append((turn.model_dump(), turn_wav))

    logger.info("Mixing audio tracks with background music ducking...")
    master_wav, timestamps, duration = mix_podcast_episode(
        turn_audio_bytes_list=turn_audio_list,
        music_track_name="chill_ambient.wav",
        music_volume=0.10,
    )

    out_file = settings.SAMPLES_DIR / output_name
    out_file.write_bytes(master_wav)

    # Save transcripts & show notes
    base_stem = out_file.stem
    srt_file = settings.SAMPLES_DIR / f"{base_stem}.srt"
    srt_file.write_text(generate_srt(timestamps), encoding="utf-8")

    logger.info(f"DEMO COMPLETE! Saved sample episode to: {out_file} ({len(master_wav)} bytes, {duration:.1f}s)")
    return str(out_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PodcastAI Demo Generator")
    parser.add_argument("--demo", action="store_true", help="Run 1-minute 2-speaker sample generation")
    parser.add_argument("--lang", choices=["en", "hi", "all"], default="all", help="Target language (en, hi, or all)")
    args = parser.parse_args()

    async def main():
        if args.lang in ["en", "all"]:
            await generate_demo_episode("en-IN", "sample_english.wav")
        if args.lang in ["hi", "all"]:
            await generate_demo_episode("hi-IN", "sample_hindi.wav")

    asyncio.run(main())


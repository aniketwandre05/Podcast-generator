import asyncio
import json
import logging
import os
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional
from app.audio.exporter import (
    convert_wav_to_mp3,
    generate_show_notes_markdown,
    generate_srt,
    generate_vtt,
)
from app.audio.mixer import mix_podcast_episode
from app.core.config import settings
from app.core.database import SessionLocal
from app.llm.script_generator import generate_episode_outline, generate_full_script
from app.models.episode import Episode
from app.models.schemas import Script
from app.research.provider import (
    DocumentResearchProvider,
    WebUrlResearchProvider,
    summarize_and_build_brief,
)
from app.sarvam.tts import synthesize_turn_text

logger = logging.getLogger("podcastai.pipeline")

# In-memory pub/sub for SSE listeners
episode_event_subscribers: Dict[str, List[asyncio.Queue]] = {}

def subscribe_to_episode(episode_id: str) -> asyncio.Queue:
    """Register an SSE event queue for an episode."""
    if episode_id not in episode_event_subscribers:
        episode_event_subscribers[episode_id] = []
    q = asyncio.Queue()
    episode_event_subscribers[episode_id].append(q)
    return q

def unsubscribe_from_episode(episode_id: str, q: asyncio.Queue):
    """Unregister an SSE event queue."""
    if episode_id in episode_event_subscribers:
        if q in episode_event_subscribers[episode_id]:
            episode_event_subscribers[episode_id].remove(q)
        if not episode_event_subscribers[episode_id]:
            del episode_event_subscribers[episode_id]

async def publish_episode_event(episode_id: str, event_type: str, data: Dict[str, Any]):
    """Broadcast an update to all connected SSE clients."""
    if episode_id in episode_event_subscribers:
        payload = {"type": event_type, "data": data}
        for q in list(episode_event_subscribers[episode_id]):
            await q.put(payload)

def update_episode_status(
    episode_id: str,
    status: str,
    progress_percent: int,
    status_message: str,
    error_message: Optional[str] = None,
):
    """Update status in SQLite DB."""
    db = SessionLocal()
    try:
        ep = db.query(Episode).filter(Episode.id == episode_id).first()
        if ep:
            ep.status = status
            ep.progress_percent = progress_percent
            ep.status_message = status_message
            if error_message:
                ep.error_message = error_message
            db.commit()
    finally:
        db.close()

async def run_full_podcast_pipeline(episode_id: str):
    """Execute the end-to-end podcast generation job in background."""
    db = SessionLocal()
    try:
        ep = db.query(Episode).filter(Episode.id == episode_id).first()
        if not ep:
            logger.error(f"Episode {episode_id} not found in database.")
            return

        topic = ep.topic
        source_type = ep.source_type
        source_content = ep.source_content or ""
        speakers = ep.speakers_config or [
            {"speaker_id": "HOST", "display_name": "Host", "voice": "shubh", "pace": 1.0, "language_code": ep.language},
            {"speaker_id": "GUEST", "display_name": "Guest", "voice": "priya", "pace": 1.0, "language_code": ep.language},
        ]
        tone = ep.tone
        target_duration_mins = ep.target_duration_mins
        audience_level = ep.audience_level
        language = ep.language
        dialogue_style = getattr(ep, "dialogue_style", "code_mixed") or "code_mixed"
        background_music = ep.background_music
        music_volume = ep.music_volume

    finally:
        db.close()

    try:
        # Step 1: Researching (0% -> 20%)
        update_episode_status(episode_id, "researching", 10, "Extracting and synthesizing source research material...")
        await publish_episode_event(episode_id, "progress", {"status": "researching", "percent": 10, "message": "Extracting source research..."})

        raw_material = source_content
        sources_list = []
        if source_type == "url" and source_content.startswith(("http://", "https://")):
            sources_list.append(source_content)
            web_prov = WebUrlResearchProvider()
            raw_material = await web_prov.extract_text(source_content)
        elif source_type == "document" and os.path.exists(source_content):
            sources_list.append(os.path.basename(source_content))
            doc_prov = DocumentResearchProvider()
            raw_material = await doc_prov.extract_text(source_content)

        research_brief = await summarize_and_build_brief(raw_material, topic, sources_list)
        
        db = SessionLocal()
        try:
            ep = db.query(Episode).filter(Episode.id == episode_id).first()
            if ep:
                ep.research_brief = research_brief
                db.commit()
        finally:
            db.close()

        # Step 2: Outlining (20% -> 35%)
        update_episode_status(episode_id, "outlining", 25, "Architecting narrative structure and segments...")
        await publish_episode_event(episode_id, "progress", {"status": "outlining", "percent": 25, "message": "Structuring outline..."})

        outline = await generate_episode_outline(
            topic=topic,
            research_brief=research_brief,
            tone=tone,
            target_duration_mins=target_duration_mins,
            audience_level=audience_level,
            speakers=speakers,
            language=language,
            dialogue_style=dialogue_style,
        )

        db = SessionLocal()
        try:
            ep = db.query(Episode).filter(Episode.id == episode_id).first()
            if ep:
                ep.title = outline.title
                ep.description = f"{outline.hook} {outline.recap}"
                ep.outline = outline.model_dump()
                db.commit()
        finally:
            db.close()

        # Step 3: Script Writing (35% -> 65%)
        def on_script_progress(msg: str, pct: int):
            update_episode_status(episode_id, "writing", pct, msg)
            asyncio.create_task(publish_episode_event(episode_id, "progress", {"status": "writing", "percent": pct, "message": msg}))

        script = await generate_full_script(
            topic=topic,
            outline=outline,
            speakers=speakers,
            tone=tone,
            language=language,
            dialogue_style=dialogue_style,
            on_progress=on_script_progress,
        )

        db = SessionLocal()
        try:
            ep = db.query(Episode).filter(Episode.id == episode_id).first()
            if ep:
                ep.script = script.model_dump()
                db.commit()
        finally:
            db.close()

        await publish_episode_event(episode_id, "script_ready", {"script": script.model_dump()})

        # Step 4: Synthesizing Audio (65% -> 88%)
        update_episode_status(episode_id, "synthesizing", 68, "Synthesizing dialogue with Sarvam Bulbul...")
        await publish_episode_event(episode_id, "progress", {"status": "synthesizing", "percent": 68, "message": "Beginning voice synthesis..."})

        # Build speaker lookup
        speaker_map = {s.get("speaker_id"): s for s in speakers}

        all_turns = []
        for seg in script.segments:
            for turn in seg.turns:
                all_turns.append(turn)

        total_turns = len(all_turns)
        turn_audio_list = []

        for idx, turn in enumerate(all_turns):
            pct = 68 + int(((idx + 1) / max(1, total_turns)) * 20) # 68% -> 88%
            update_episode_status(episode_id, "synthesizing", pct, f"Synthesizing turn {idx + 1}/{total_turns} ({turn.speaker})...")
            await publish_episode_event(episode_id, "progress", {"status": "synthesizing", "percent": pct, "message": f"Synthesizing turn {idx + 1}/{total_turns}..."})

            sp_config = speaker_map.get(turn.speaker, speakers[0])
            voice = sp_config.get("voice", "shubh")
            pace = float(sp_config.get("pace", 1.0))
            turn_lang = turn.language_code or sp_config.get("language_code", language)

            # Synthesize turn (handling internal chunking if sentence exceeds limits)
            audio_chunks = await synthesize_turn_text(
                text=turn.text,
                voice=voice,
                language_code=turn_lang,
                pace=pace,
                model="bulbul:v3",
            )
            # Combine any sub-chunks
            if len(audio_chunks) == 1:
                turn_wav = audio_chunks[0]
            else:
                from app.audio.processor import read_wav_bytes, write_wav_bytes
                combined = []
                for c in audio_chunks:
                    arr, sr = read_wav_bytes(c)
                    combined.append(arr)
                import numpy as np
                turn_wav = write_wav_bytes(np.concatenate(combined))

            turn_audio_list.append((turn.model_dump(), turn_wav))

        # Step 5: Mixing & Production (88% -> 98%)
        update_episode_status(episode_id, "mixing", 90, "Stitching audio, balancing loudness, and ducking music...")
        await publish_episode_event(episode_id, "progress", {"status": "mixing", "percent": 90, "message": "Mixing and mastering episode..."})

        master_wav_bytes, turn_timestamps, duration_s = mix_podcast_episode(
            turn_audio_bytes_list=turn_audio_list,
            music_track_name=background_music,
            music_volume=music_volume,
        )

        # Save master audio files
        ep_dir = settings.STORAGE_DIR / episode_id
        ep_dir.mkdir(parents=True, exist_ok=True)
        
        wav_file_path = ep_dir / "master.wav"
        wav_file_path.write_bytes(master_wav_bytes)

        # Export transcripts
        srt_content = generate_srt(turn_timestamps)
        (ep_dir / "transcript.srt").write_text(srt_content, encoding="utf-8")

        vtt_content = generate_vtt(turn_timestamps)
        (ep_dir / "transcript.vtt").write_text(vtt_content, encoding="utf-8")

        (ep_dir / "transcript.json").write_text(json.dumps(turn_timestamps, indent=2), encoding="utf-8")

        show_notes_md = generate_show_notes_markdown(
            title=script.title,
            topic=topic,
            duration_s=duration_s,
            research_brief=research_brief,
            outline=outline.model_dump(),
            turn_timestamps=turn_timestamps,
        )
        (ep_dir / "show_notes.md").write_text(show_notes_md, encoding="utf-8")

        # Convert to MP3 if possible
        mp3_file_path = ep_dir / "master.mp3"
        convert_wav_to_mp3(
            str(wav_file_path),
            str(mp3_file_path),
            metadata={"title": script.title, "description": script.description},
        )

        # Step 6: Completed (100%)
        db = SessionLocal()
        try:
            ep = db.query(Episode).filter(Episode.id == episode_id).first()
            if ep:
                ep.audio_path = str(wav_file_path)
                ep.duration_seconds = duration_s
                ep.status = "completed"
                ep.progress_percent = 100
                ep.status_message = "Episode ready!"
                db.commit()
        finally:
            db.close()

        update_episode_status(episode_id, "completed", 100, "Episode ready!")
        await publish_episode_event(episode_id, "completed", {
            "duration_seconds": duration_s,
            "audio_url": f"/api/episodes/{episode_id}/export?format=wav",
        })

    except Exception as e:
        logger.exception(f"Pipeline error on episode {episode_id}: {e}")
        update_episode_status(episode_id, "failed", 0, "Generation failed", error_message=str(e))
        await publish_episode_event(episode_id, "error", {"error": str(e)})

async def regenerate_episode_audio(episode_id: str):
    """Regenerate only audio from updated script without rewriting text."""
    db = SessionLocal()
    try:
        ep = db.query(Episode).filter(Episode.id == episode_id).first()
        if not ep or not ep.script:
            return
        script_dict = ep.script
        speakers = ep.speakers_config
        background_music = ep.background_music
        music_volume = ep.music_volume
        language = ep.language
    finally:
        db.close()

    script = Script(**script_dict)
    speaker_map = {s.get("speaker_id"): s for s in speakers}

    all_turns = []
    for seg in script.segments:
        for turn in seg.turns:
            all_turns.append(turn)

    total_turns = len(all_turns)
    turn_audio_list = []

    update_episode_status(episode_id, "synthesizing", 10, "Regenerating audio for turns...")
    await publish_episode_event(episode_id, "progress", {"status": "synthesizing", "percent": 10, "message": "Synthesizing modified turns..."})

    for idx, turn in enumerate(all_turns):
        pct = 10 + int(((idx + 1) / max(1, total_turns)) * 75)
        update_episode_status(episode_id, "synthesizing", pct, f"Turn {idx + 1}/{total_turns}...")
        await publish_episode_event(episode_id, "progress", {"status": "synthesizing", "percent": pct, "message": f"Turn {idx + 1}/{total_turns}..."})

        sp_config = speaker_map.get(turn.speaker, speakers[0])
        voice = sp_config.get("voice", "shubh")
        pace = float(sp_config.get("pace", 1.0))
        turn_lang = turn.language_code or sp_config.get("language_code", language)

        audio_chunks = await synthesize_turn_text(
            text=turn.text,
            voice=voice,
            language_code=turn_lang,
            pace=pace,
            model="bulbul:v3",
        )
        if len(audio_chunks) == 1:
            turn_wav = audio_chunks[0]
        else:
            from app.audio.processor import read_wav_bytes, write_wav_bytes
            import numpy as np
            combined = [read_wav_bytes(c)[0] for c in audio_chunks]
            turn_wav = write_wav_bytes(np.concatenate(combined))

        turn_audio_list.append((turn.model_dump(), turn_wav))

    update_episode_status(episode_id, "mixing", 90, "Re-mixing episode...")
    master_wav_bytes, turn_timestamps, duration_s = mix_podcast_episode(
        turn_audio_bytes_list=turn_audio_list,
        music_track_name=background_music,
        music_volume=music_volume,
    )

    ep_dir = settings.STORAGE_DIR / episode_id
    ep_dir.mkdir(parents=True, exist_ok=True)
    wav_file_path = ep_dir / "master.wav"
    wav_file_path.write_bytes(master_wav_bytes)

    (ep_dir / "transcript.srt").write_text(generate_srt(turn_timestamps), encoding="utf-8")
    (ep_dir / "transcript.vtt").write_text(generate_vtt(turn_timestamps), encoding="utf-8")
    (ep_dir / "transcript.json").write_text(json.dumps(turn_timestamps, indent=2), encoding="utf-8")

    db = SessionLocal()
    try:
        ep = db.query(Episode).filter(Episode.id == episode_id).first()
        if ep:
            ep.duration_seconds = duration_s
            ep.status = "completed"
            ep.progress_percent = 100
            ep.status_message = "Audio updated!"
            db.commit()
    finally:
        db.close()

    update_episode_status(episode_id, "completed", 100, "Audio updated!")
    await publish_episode_event(episode_id, "completed", {
        "duration_seconds": duration_s,
        "audio_url": f"/api/episodes/{episode_id}/export?format=wav",
    })


import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.episode import Episode
from app.models.schemas import (
    EpisodeCreateRequest,
    EpisodeResponse,
    ScriptUpdateRequest,
    TranslateEpisodeRequest,
    TurnTranslateRequest,
)
from app.pipeline.generator import regenerate_episode_audio, run_full_podcast_pipeline
from app.sarvam.translate import translate_text

router = APIRouter(prefix="/api/episodes", tags=["episodes"])

def serialize_episode(ep: Episode) -> Dict[str, Any]:
    return {
        "id": ep.id,
        "title": ep.title,
        "description": ep.description,
        "topic": ep.topic,
        "source_type": ep.source_type,
        "language": ep.language,
        "dialogue_style": getattr(ep, "dialogue_style", "code_mixed") or "code_mixed",
        "tone": ep.tone,
        "target_duration_mins": ep.target_duration_mins,
        "speakers_config": ep.speakers_config,
        "research_brief": ep.research_brief,
        "outline": ep.outline,
        "script": ep.script,
        "audio_path": ep.audio_path,
        "audio_url": f"/api/episodes/{ep.id}/export?format=wav" if ep.audio_path else None,
        "duration_seconds": ep.duration_seconds,
        "status": ep.status,
        "progress_percent": ep.progress_percent,
        "status_message": ep.status_message,
        "error_message": ep.error_message,
        "created_at": ep.created_at.isoformat() if ep.created_at else "",
        "updated_at": ep.updated_at.isoformat() if ep.updated_at else "",
    }

@router.get("", response_model=List[Dict[str, Any]])
def list_episodes(db: Session = Depends(get_db)):
    episodes = db.query(Episode).order_by(Episode.created_at.desc()).all()
    return [serialize_episode(ep) for ep in episodes]

@router.get("/{episode_id}")
def get_episode(episode_id: str, db: Session = Depends(get_db)):
    ep = db.query(Episode).filter(Episode.id == episode_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")
    return serialize_episode(ep)

@router.post("")
def create_episode(
    req: EpisodeCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    episode_id = str(uuid.uuid4())
    
    speakers_data = [s.model_dump() for s in req.speakers] if req.speakers else [
        {"speaker_id": "HOST", "display_name": "Host", "voice": "shubh", "pace": 1.0, "language_code": req.language},
        {"speaker_id": "GUEST", "display_name": "Guest", "voice": "priya", "pace": 1.0, "language_code": req.language},
    ]

    ep = Episode(
        id=episode_id,
        title=f"Episode: {req.topic[:40]}...",
        topic=req.topic,
        source_type=req.source_type,
        source_content=req.source_content or "",
        language=req.language,
        dialogue_style=req.dialogue_style,
        tone=req.tone,
        target_duration_mins=req.target_duration_mins,
        audience_level=req.audience_level,
        background_music=req.background_music,
        music_volume=req.music_volume,
        status="created",
        progress_percent=0,
        status_message="Episode queued",
    )
    ep.speakers_config = speakers_data

    db.add(ep)
    db.commit()
    db.refresh(ep)

    background_tasks.add_task(run_full_podcast_pipeline, episode_id)
    return serialize_episode(ep)

@router.put("/{episode_id}/script")
def update_script(
    episode_id: str,
    req: ScriptUpdateRequest,
    db: Session = Depends(get_db),
):
    ep = db.query(Episode).filter(Episode.id == episode_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    ep.script = req.script.model_dump()
    ep.title = req.script.title
    ep.description = req.script.description
    db.commit()
    return {"status": "success", "message": "Script updated successfully"}

@router.post("/{episode_id}/synthesize")
def trigger_resynthesis(
    episode_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    ep = db.query(Episode).filter(Episode.id == episode_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")

    background_tasks.add_task(regenerate_episode_audio, episode_id)
    return {"status": "processing", "message": "Audio re-synthesis started"}

@router.post("/{episode_id}/translate")
async def translate_episode(
    episode_id: str,
    req: TranslateEpisodeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    ep = db.query(Episode).filter(Episode.id == episode_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    script_data = ep.script
    if not script_data:
        raise HTTPException(status_code=400, detail="Episode has no script to translate")

    source_lang = ep.language
    target_lang = req.target_language_code

    # Translate title & description
    translated_title = await translate_text(script_data.get("title", ""), source_lang, target_lang, req.mode)
    translated_desc = await translate_text(script_data.get("description", ""), source_lang, target_lang, req.mode)

    # Translate each turn in segments
    segments = script_data.get("segments", [])
    for seg in segments:
        seg["name"] = await translate_text(seg.get("name", ""), source_lang, target_lang, req.mode)
        for turn in seg.get("turns", []):
            original_text = turn.get("text", "")
            turn["text"] = await translate_text(original_text, source_lang, target_lang, req.mode)
            turn["language_code"] = target_lang

    script_data["title"] = translated_title
    script_data["description"] = translated_desc
    script_data["segments"] = segments

    ep.title = translated_title
    ep.description = translated_desc
    ep.script = script_data
    ep.language = target_lang

    if req.update_speakers and ep.speakers_config:
        updated_speakers = []
        for s in ep.speakers_config:
            s_copy = dict(s)
            s_copy["language_code"] = target_lang
            updated_speakers.append(s_copy)
        ep.speakers_config = updated_speakers

    db.commit()

    # Re-synthesize with translated script
    background_tasks.add_task(regenerate_episode_audio, episode_id)
    return {"status": "success", "message": f"Script translated to {target_lang}. Audio re-synthesis triggered."}

@router.post("/translate-turn")
async def translate_single_turn(req: TurnTranslateRequest):
    """Translate an individual dialogue turn or text snippet on the fly."""
    translated = await translate_text(
        text=req.text,
        source_language_code=req.source_language_code,
        target_language_code=req.target_language_code,
        mode=req.mode,
    )
    return {
        "original_text": req.text,
        "translated_text": translated,
        "source_language_code": req.source_language_code,
        "target_language_code": req.target_language_code,
        "mode": req.mode,
    }

@router.delete("/{episode_id}")
def delete_episode(episode_id: str, db: Session = Depends(get_db)):
    ep = db.query(Episode).filter(Episode.id == episode_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")
    db.delete(ep)
    db.commit()
    return {"status": "deleted", "id": episode_id}

@router.post("/{episode_id}/duplicate")
def duplicate_episode(
    episode_id: str,
    db: Session = Depends(get_db),
):
    ep = db.query(Episode).filter(Episode.id == episode_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")

    new_id = str(uuid.uuid4())
    clone = Episode(
        id=new_id,
        title=f"Copy of {ep.title}",
        topic=ep.topic,
        source_type=ep.source_type,
        source_content=ep.source_content,
        language=ep.language,
        tone=ep.tone,
        target_duration_mins=ep.target_duration_mins,
        audience_level=ep.audience_level,
        background_music=ep.background_music,
        music_volume=ep.music_volume,
        status="completed" if ep.status == "completed" else "created",
        progress_percent=ep.progress_percent,
        status_message=ep.status_message,
        duration_seconds=ep.duration_seconds,
        audio_path=ep.audio_path,
    )
    clone.speakers_config = ep.speakers_config
    clone.research_brief = ep.research_brief
    clone.outline = ep.outline
    clone.script = ep.script

    db.add(clone)
    db.commit()
    return serialize_episode(clone)


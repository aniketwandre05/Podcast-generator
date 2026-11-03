import asyncio
import json
import logging
from pathlib import Path
import re
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.episode import Episode
from app.models.schemas import (
    EpisodeCreateRequest,
    EpisodeResponse,
    ExtractUrlRequest,
    ScriptUpdateRequest,
    SourceItem,
    TranslateEpisodeRequest,
    TurnTranslateRequest,
)
from app.pipeline.generator import regenerate_episode_audio, run_full_podcast_pipeline
from app.research.provider import (
    DocumentResearchProvider,
    WebUrlResearchProvider,
    YouTubeResearchProvider,
    is_youtube_url,
)
from app.sarvam.translate import translate_text

logger = logging.getLogger("podcastai.api.episodes")

router = APIRouter(prefix="/api/episodes", tags=["episodes"])

def serialize_episode(ep: Episode) -> Dict[str, Any]:
    return {
        "id": ep.id,
        "title": ep.title,
        "description": ep.description,
        "topic": ep.topic,
        "source_type": ep.source_type,
        "sources": getattr(ep, "sources", []),
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

    sources_data = [s.model_dump() for s in req.sources] if req.sources else []
    resolved_source_type = req.source_type
    if sources_data and resolved_source_type == "prompt":
        resolved_source_type = "multi_source"

    ep = Episode(
        id=episode_id,
        title=f"Episode: {req.topic[:40]}...",
        topic=req.topic,
        source_type=resolved_source_type,
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
    ep.sources = sources_data

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

@router.post("/upload-doc")
async def upload_document(file: UploadFile = File(...)):
    """Upload and extract text from document (PDF, DOCX, TXT, MD)."""
    filename = file.filename or "uploaded_document"
    ext = Path(filename).suffix.lower()
    
    if ext not in [".pdf", ".docx", ".txt", ".md"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported formats: .pdf, .docx, .txt, .md",
        )
    
    contents = await file.read()
    if len(contents) > 25 * 1024 * 1024: # 25 MB limit
        raise HTTPException(status_code=400, detail="File too large. Maximum supported file size is 25MB.")
    
    temp_dir = settings.DATA_DIR / "uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    clean_stem = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", Path(filename).stem)[:50]
    saved_filename = f"{uuid.uuid4().hex[:8]}_{clean_stem}{ext}"
    temp_file = temp_dir / saved_filename
    temp_file.write_bytes(contents)
    
    try:
        prov = DocumentResearchProvider()
        extracted_text = await prov.extract_text(str(temp_file))
        cleaned_text = re.sub(r"\s+", " ", extracted_text).strip()
        words = len(cleaned_text.split()) if cleaned_text else 0
        
        # Suggested title from filename
        suggested_title = Path(filename).stem.replace("_", " ").replace("-", " ").strip()
        suggested_title = re.sub(r"\s+", " ", suggested_title).title()
        
        return {
            "status": "success",
            "filename": filename,
            "file_size": len(contents),
            "file_type": ext.lstrip("."),
            "extracted_text": cleaned_text,
            "word_count": words,
            "char_count": len(cleaned_text),
            "saved_path": str(temp_file),
            "suggested_title": suggested_title,
        }
    except Exception as e:
        logger.error(f"Failed to process document {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract document content: {str(e)}")

@router.post("/upload-docs")
async def upload_multiple_documents(files: List[UploadFile] = File(...)):
    """Upload and extract text from multiple documents (PDF, DOCX, TXT, MD) simultaneously."""
    valid_files = [f for f in files if Path(f.filename or "").suffix.lower() in [".pdf", ".docx", ".txt", ".md"]]
    if not valid_files:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Supported formats: .pdf, .docx, .txt, .md",
        )

    results = []
    temp_dir = settings.DATA_DIR / "uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    prov = DocumentResearchProvider()

    for file in valid_files:
        filename = file.filename or "uploaded_document"
        ext = Path(filename).suffix.lower()
        if ext not in [".pdf", ".docx", ".txt", ".md"]:
            continue

        contents = await file.read()
        if len(contents) > 25 * 1024 * 1024:
            continue

        clean_stem = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", Path(filename).stem)[:50]
        temp_file = temp_dir / f"{uuid.uuid4().hex[:8]}_{clean_stem}{ext}"
        temp_file.write_bytes(contents)

        try:
            extracted_text = await prov.extract_text(str(temp_file))
            cleaned_text = re.sub(r"\s+", " ", extracted_text).strip()
            words = len(cleaned_text.split()) if cleaned_text else 0
            suggested_title = Path(filename).stem.replace("_", " ").replace("-", " ").strip().title()

            results.append({
                "id": str(uuid.uuid4()),
                "source_type": "file",
                "title": suggested_title or filename,
                "content": str(temp_file),
                "extracted_preview": cleaned_text[:300] + ("..." if len(cleaned_text) > 300 else ""),
                "file_type": ext.lstrip("."),
                "file_size": len(contents),
                "word_count": words,
                "filename": filename,
            })
        except Exception as e:
            logger.warning(f"Failed to process document {filename}: {e}")

    return {
        "status": "success",
        "sources": results,
        "total_files": len(results),
    }

@router.post("/extract-url")
async def extract_url_content(req: ExtractUrlRequest):
    """Extract research content from any web article or YouTube video (with transcripts)."""
    url = req.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format. URL must start with http:// or https://")

    if is_youtube_url(url):
        yt_prov = YouTubeResearchProvider()
        info = await yt_prov.extract_info(url)
        if info.get("status") != "success":
            raise HTTPException(status_code=400, detail=info.get("message", "Could not process YouTube URL"))

        return {
            "status": "success",
            "source_type": "youtube",
            "title": info.get("title"),
            "author": info.get("author"),
            "content": info.get("content"),
            "url": url,
            "has_transcript": info.get("has_transcript", False),
            "word_count": info.get("word_count", 0),
        }
    else:
        web_prov = WebUrlResearchProvider()
        text = await web_prov.extract_text(url)
        words = len(text.split()) if text else 0

        title_match = re.search(r"^Title:\s*(.+)$", text, re.MULTILINE)
        extracted_title = title_match.group(1).strip() if title_match else url

        return {
            "status": "success",
            "source_type": "url",
            "title": extracted_title,
            "content": text,
            "url": url,
            "has_transcript": False,
            "word_count": words,
        }


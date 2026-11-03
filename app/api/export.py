import json
import os
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.episode import Episode

router = APIRouter(prefix="/api/episodes", tags=["export"])

@router.get("/{episode_id}/export")
def export_episode(
    episode_id: str,
    format: str = Query("wav", pattern="^(wav|mp3|srt|vtt|md|json)$"),
    db: Session = Depends(get_db),
):
    """Download episode assets in WAV, MP3, SRT, VTT, MD, or JSON."""
    ep = db.query(Episode).filter(Episode.id == episode_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")

    ep_dir = settings.STORAGE_DIR / episode_id
    if not ep_dir.exists():
        raise HTTPException(status_code=404, detail="Episode files not generated yet")

    clean_title = "".join(c for c in ep.title if c.isalnum() or c in " _-").strip() or "episode"

    if format == "wav":
        wav_path = ep_dir / "master.wav"
        if not wav_path.exists():
            raise HTTPException(status_code=404, detail="WAV audio not found")
        return FileResponse(
            path=str(wav_path),
            media_type="audio/wav",
            filename=f"{clean_title}.wav",
        )

    elif format == "mp3":
        mp3_path = ep_dir / "master.mp3"
        # If mp3 exists, return it; otherwise fallback to wav
        if mp3_path.exists():
            return FileResponse(
                path=str(mp3_path),
                media_type="audio/mpeg",
                filename=f"{clean_title}.mp3",
            )
        wav_path = ep_dir / "master.wav"
        if wav_path.exists():
            return FileResponse(
                path=str(wav_path),
                media_type="audio/wav",
                filename=f"{clean_title}.wav",
            )
        raise HTTPException(status_code=404, detail="Audio file not found")

    elif format == "srt":
        srt_path = ep_dir / "transcript.srt"
        if not srt_path.exists():
            raise HTTPException(status_code=404, detail="SRT transcript not found")
        return FileResponse(
            path=str(srt_path),
            media_type="text/plain; charset=utf-8",
            filename=f"{clean_title}.srt",
        )

    elif format == "vtt":
        vtt_path = ep_dir / "transcript.vtt"
        if not vtt_path.exists():
            raise HTTPException(status_code=404, detail="VTT transcript not found")
        return FileResponse(
            path=str(vtt_path),
            media_type="text/vtt; charset=utf-8",
            filename=f"{clean_title}.vtt",
        )

    elif format == "md":
        md_path = ep_dir / "show_notes.md"
        if not md_path.exists():
            raise HTTPException(status_code=404, detail="Show notes not found")
        return FileResponse(
            path=str(md_path),
            media_type="text/markdown; charset=utf-8",
            filename=f"{clean_title}_show_notes.md",
        )

    elif format == "json":
        script_data = ep.script
        return Response(
            content=json.dumps(script_data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{clean_title}_script.json"'},
        )


import logging
import re
from typing import Any, Callable, Dict, List, Optional
from app.llm.prompts import get_outline_system_prompt, get_segment_script_prompt
from app.models.schemas import Outline, Script, Segment, Turn
from app.sarvam.llm import generate_structured_json

logger = logging.getLogger("podcastai.script")

def sanitize_turn_text(text: str) -> str:
    """Strip accidental stage directions and brackets like [laughter] or (laughs)."""
    # Remove bracketed and parenthesized stage directions
    cleaned = re.sub(r"\[[^\]]*\]", "", text)
    cleaned = re.sub(r"\([^\)]*\)", "", cleaned)
    cleaned = re.sub(r"\*[^\*]*\*", "", cleaned)
    # Clean whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

async def generate_episode_outline(
    topic: str,
    research_brief: Dict[str, Any],
    tone: str = "casual",
    target_duration_mins: int = 5,
    audience_level: str = "general",
    speakers: List[Dict[str, Any]] = None,
    language: str = "en-IN",
    dialogue_style: str = "code_mixed",
    on_progress: Optional[Callable[[str, int], None]] = None,
) -> Outline:
    """Step A: Generate comprehensive episode outline."""
    if on_progress:
        on_progress("Developing episode structure & narrative arc...", 25)

    speakers = speakers or [{"speaker_id": "HOST", "display_name": "Host"}]
    sys_prompt = get_outline_system_prompt(
        tone=tone,
        target_duration_mins=target_duration_mins,
        audience_level=audience_level,
        num_speakers=len(speakers),
        language=language,
        dialogue_style=dialogue_style,
    )

    speaker_descs = [f"{s.get('display_name')} ({s.get('language_code', language)})" for s in speakers]
    user_prompt = (
        f"Topic: {topic}\n\n"
        f"Research Brief Key Facts: {research_brief.get('key_facts', [])}\n"
        f"Key Points: {research_brief.get('key_points', [])}\n"
        f"Interesting Angles: {research_brief.get('interesting_angles', [])}\n"
        f"Speakers: {speaker_descs}"
    )

    data = await generate_structured_json([
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt},
    ])

    return Outline(**data)

async def generate_full_script(
    topic: str,
    outline: Outline,
    speakers: List[Dict[str, Any]],
    tone: str = "casual",
    language: str = "en-IN",
    dialogue_style: str = "code_mixed",
    on_progress: Optional[Callable[[str, int], None]] = None,
) -> Script:
    """Step B: Generate script segment by segment for narrative continuity."""
    segments_to_build = []
    
    # 1. Cold Open & Intro
    segments_to_build.append({
        "name": "Cold Open & Intro",
        "goal": f"Hook: {outline.hook} | Intro: {outline.intro}"
    })
    
    # 2. Outline Segments
    for seg in outline.segments:
        segments_to_build.append({
            "name": seg.title,
            "goal": f"{seg.goal}. Key Points: {', '.join(seg.key_points)}"
        })

    # 3. Recap & Outro
    segments_to_build.append({
        "name": "Recap & Outro",
        "goal": f"Recap: {outline.recap} | Outro: {outline.outro}"
    })

    built_segments: List[Segment] = []
    prev_summary = ""
    total_segs = len(segments_to_build)
    speaker_lang_map = {s.get("speaker_id"): s.get("language_code", language) for s in speakers}

    for idx, seg_info in enumerate(segments_to_build):
        progress_pct = 35 + int(((idx + 1) / total_segs) * 30) # 35% -> 65%
        if on_progress:
            on_progress(f"Writing script: Segment {idx + 1}/{total_segs} ({seg_info['name']})...", progress_pct)

        sys_prompt = get_segment_script_prompt(
            segment_name=seg_info["name"],
            segment_goal=seg_info["goal"],
            speakers=speakers,
            tone=tone,
            language=language,
            dialogue_style=dialogue_style,
            previous_summary=prev_summary,
        )

        user_prompt = f"Write the natural dialogue turns for segment: \"{seg_info['name']}\"."
        
        seg_data = await generate_structured_json([
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ])

        turns = []
        for t in seg_data.get("turns", []):
            raw_text = t.get("text", "")
            cleaned_text = sanitize_turn_text(raw_text)
            if cleaned_text:
                sp_id = t.get("speaker", speakers[0].get("speaker_id", "HOST"))
                turn_lang = t.get("language_code") or speaker_lang_map.get(sp_id, language)
                turns.append(Turn(
                    speaker=sp_id,
                    text=cleaned_text,
                    emotion=t.get("emotion", "natural"),
                    pause_after_ms=t.get("pause_after_ms", 350),
                    language_code=turn_lang,
                ))

        segment = Segment(
            name=seg_info["name"],
            summary=seg_data.get("summary", ""),
            turns=turns,
        )
        built_segments.append(segment)
        prev_summary = segment.summary

    return Script(
        title=outline.title,
        description=f"{outline.hook} {outline.recap}",
        segments=built_segments,
    )


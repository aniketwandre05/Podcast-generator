import json
from typing import Any, Dict, List

def get_outline_system_prompt(
    tone: str,
    target_duration_mins: int,
    audience_level: str,
    num_speakers: int,
    language: str,
    dialogue_style: str = "code_mixed",
) -> str:
    # Estimate words: ~150 words per minute
    target_words = target_duration_mins * 150
    num_segments = 3 if target_duration_mins <= 5 else (4 if target_duration_mins <= 10 else 5)

    style_desc = (
        "Modern Conversational Code-Mixed (natural blend of Indic & conversational English)"
        if dialogue_style == "code_mixed"
        else (
            "Pure Native Script & Regional Idiom"
            if dialogue_style == "native"
            else (
                "Bilingual / Multilingual Panel Discussion"
                if dialogue_style == "bilingual"
                else "Contemporary Indian English"
            )
        )
    )

    return (
        f"You are an award-winning executive podcast producer creating a structured episode outline.\n"
        f"Episode Tone: {tone}\n"
        f"Target Duration: {target_duration_mins} minutes (~{target_words} total words across the episode)\n"
        f"Audience Level: {audience_level}\n"
        f"Number of Speakers: {num_speakers}\n"
        f"Primary Language: {language}\n"
        f"Dialogue Style: {style_desc}\n\n"
        f"Instructions:\n"
        f"1. Design a compelling episode structure:\n"
        f"   - Cold Open / Hook: Intriguing teaser or punchy question to hook listeners immediately.\n"
        f"   - Intro: Welcome, topic setup, and guest/co-host introduction.\n"
        f"   - {num_segments} Core Segments: Logical progression from fundamentals to deep insights or debates.\n"
        f"   - Recap: Crisp takeaways for the audience.\n"
        f"   - Outro: Call to action, sign-off.\n"
        f"2. Return ONLY valid JSON matching this schema:\n"
        f"{{\n"
        f'  "title": "Punchy, Catchy Title",\n'
        f'  "hook": "Teaser concept...",\n'
        f'  "intro": "Episode setup...",\n'
        f'  "segments": [\n'
        f'    {{"title": "Segment 1 Title", "goal": "What listeners discover...", "key_points": ["point A", "point B"]}},\n'
        f'    ...\n'
        f'  ],\n'
        f'  "recap": "Key conclusions...",\n'
        f'  "outro": "Signoff and listener CTA..."\n'
        f"}}"
    )

def get_segment_script_prompt(
    segment_name: str,
    segment_goal: str,
    speakers: List[Dict[str, Any]],
    tone: str,
    language: str,
    dialogue_style: str = "code_mixed",
    previous_summary: str = "",
) -> str:
    speakers_info = "\n".join([
        f"- {s.get('speaker_id', 'SPEAKER')}: {s.get('display_name', 'Host')} (Assigned Language: {s.get('language_code', language)}, Voice: {s.get('voice', 'default')})"
        for s in speakers
    ])

    # Distinct languages across speakers
    distinct_langs = list(dict.fromkeys(s.get('language_code', language) for s in speakers))
    is_multi_speaker_lang = len(distinct_langs) > 1

    if is_multi_speaker_lang or dialogue_style == "bilingual":
        style_guidelines = (
            "MULTILINGUAL / BILINGUAL SHOW DYNAMIC:\n"
            "- Each speaker MUST speak in their assigned language specified in the cast list.\n"
            "- For example, if Speaker 1 is en-IN and Speaker 2 is hi-IN, Speaker 1 speaks in English and Speaker 2 responds naturally in Hindi/Hinglish.\n"
            "- Both speakers fully understand each other and build directly upon each other's ideas."
        )
    elif dialogue_style == "code_mixed" or (language == "hi-IN" and dialogue_style != "native"):
        style_guidelines = (
            "CONVERSATIONAL CODE-MIXED (Hinglish/Tanglish style):\n"
            "- Use natural, contemporary conversational phrasing as heard on leading Indian podcasts (The Seen and the Unseen, Cyrus Says, Ranveer Show, Finshots).\n"
            "- Seamlessly blend modern vocabulary ('actually', 'ground reality', 'fundamentally', 'market dynamics', 'interesting angle') with Indic grammar.\n"
            "- Do NOT use overly formal, archaic, or textbook-stiff vocabulary."
        )
    elif dialogue_style == "native":
        style_guidelines = (
            f"PURE NATIVE SCRIPT ({language}):\n"
            f"- Write natively and idiomatically in the authentic script of {language}.\n"
            "- Use culturally authentic phrasing and regional expressions."
        )
    else:
        style_guidelines = (
            "CONTEMPORARY INDIAN ENGLISH (en-IN):\n"
            "- Write in crisp, engaging contemporary Indian English with sharp pacing, natural banter, and relatable metaphors."
        )

    return (
        f"You are a master podcast scriptwriter writing dialogue for a hit show.\n"
        f"Current Segment: \"{segment_name}\"\n"
        f"Segment Goal: {segment_goal}\n"
        f"Previous Segment Summary: {previous_summary or 'Starting segment'}\n"
        f"Tone: {tone}\n\n"
        f"Cast of Speakers:\n{speakers_info}\n\n"
        f"{style_guidelines}\n\n"
        f"CRITICAL DIALOGUE RULES:\n"
        f"1. Spoken dialogue ONLY. NEVER write stage directions or sound effects (NO '[laughter]', '(chuckles)', '*laughs*', '[music swells]', or parentheticals). The TTS engine speaks every word literally!\n"
        f"2. Natural conversation dynamics: use short turns (1-3 sentences per turn), genuine back-and-forth reactions ('Exactly!', 'Wait, but how?', 'Oh wow, that is huge!'), active listening, and thoughtful questions.\n"
        f"3. No robotic bullet points or lecture monologues. Break complex thoughts into shared conversational discovery.\n"
        f"4. Assign speakers strictly from the cast: {[s.get('speaker_id') for s in speakers]}.\n"
        f"5. Output ONLY valid JSON matching this schema:\n"
        f"{{\n"
        f'  "name": "{segment_name}",\n'
        f'  "summary": "Brief 1-sentence summary of what happened",\n'
        f'  "turns": [\n'
        f'    {{"speaker": "{speakers[0].get("speaker_id")}", "text": "...", "emotion": "curious", "pause_after_ms": 300, "language_code": "{speakers[0].get("language_code", language)}"}},\n'
        f'    {{"speaker": "{speakers[1].get("speaker_id") if len(speakers) > 1 else speakers[0].get("speaker_id")}", "text": "...", "emotion": "excited", "pause_after_ms": 350, "language_code": "{speakers[1].get("language_code", language) if len(speakers) > 1 else speakers[0].get("language_code", language)}"}}\n'
        f'  ]\n'
        f"}}"
    )


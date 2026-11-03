import json
from typing import Any, Dict, List

def get_outline_system_prompt(
    tone: str,
    target_duration_mins: int,
    audience_level: str,
    num_speakers: int,
    language: str,
) -> str:
    # Estimate words: ~150 words per minute
    target_words = target_duration_mins * 150
    num_segments = 3 if target_duration_mins <= 5 else (4 if target_duration_mins <= 10 else 5)

    return (
        f"You are an award-winning executive podcast producer creating a structured episode outline.\n"
        f"Episode Tone: {tone}\n"
        f"Target Duration: {target_duration_mins} minutes (~{target_words} total words across the episode)\n"
        f"Audience Level: {audience_level}\n"
        f"Number of Speakers: {num_speakers}\n"
        f"Language / Dialect: {language}\n\n"
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
    previous_summary: str = "",
) -> str:
    speakers_info = "\n".join([
        f"- {s.get('speaker_id', 'SPEAKER')}: {s.get('display_name', 'Host')} (Role: {s.get('role', 'Speaker')})"
        for s in speakers
    ])

    lang_guidance = (
        "Write naturally in contemporary Indian English (en-IN)."
        if language == "en-IN"
        else (
            "Write in natural, conversational Hinglish / Hindi as spoken in modern podcasts."
            if language == "hi-IN"
            else f"Write natively and idiomatically in {language}."
        )
    )

    return (
        f"You are a master podcast scriptwriter writing dialogue for a hit show.\n"
        f"Current Segment: \"{segment_name}\"\n"
        f"Segment Goal: {segment_goal}\n"
        f"Previous Segment Summary: {previous_summary or 'Starting segment'}\n"
        f"Tone: {tone}\n"
        f"Language Style: {lang_guidance}\n\n"
        f"Cast of Speakers:\n{speakers_info}\n\n"
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
        f'    {{"speaker": "{speakers[0].get("speaker_id")}", "text": "...", "emotion": "curious", "pause_after_ms": 300}},\n'
        f'    {{"speaker": "{speakers[1].get("speaker_id") if len(speakers) > 1 else speakers[0].get("speaker_id")}", "text": "...", "emotion": "excited", "pause_after_ms": 350}}\n'
        f'  ]\n'
        f"}}"
    )


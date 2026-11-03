import pytest
from app.llm.prompts import get_outline_system_prompt, get_segment_script_prompt
from app.models.schemas import EpisodeCreateRequest, TurnTranslateRequest, TranslateEpisodeRequest
from app.api.voices import LANGUAGE_PREVIEW_TEXTS

def test_multilingual_preview_texts_coverage():
    expected_langs = ["en-IN", "hi-IN", "bn-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "mr-IN", "gu-IN", "pa-IN", "od-IN"]
    for lang in expected_langs:
        assert lang in LANGUAGE_PREVIEW_TEXTS, f"Missing preview text for language {lang}"
        assert len(LANGUAGE_PREVIEW_TEXTS[lang]) > 10

def test_code_mixed_prompt_generation():
    prompt = get_segment_script_prompt(
        segment_name="Tech Trends",
        segment_goal="Discuss GenAI in India",
        speakers=[
            {"speaker_id": "HOST", "display_name": "Rohan", "language_code": "hi-IN", "voice": "rohan"},
            {"speaker_id": "GUEST", "display_name": "Priya", "language_code": "hi-IN", "voice": "priya"}
        ],
        tone="casual",
        language="hi-IN",
        dialogue_style="code_mixed",
    )
    assert "CONVERSATIONAL CODE-MIXED" in prompt
    assert "Hinglish/Tanglish" in prompt
    assert "CRITICAL DIALOGUE RULES" in prompt

def test_bilingual_cross_lingual_prompt():
    prompt = get_segment_script_prompt(
        segment_name="Global Perspectives",
        segment_goal="Cross-lingual interview",
        speakers=[
            {"speaker_id": "HOST", "display_name": "Shubh", "language_code": "en-IN", "voice": "shubh"},
            {"speaker_id": "GUEST", "display_name": "Dev", "language_code": "hi-IN", "voice": "dev"}
        ],
        tone="interview",
        language="en-IN",
        dialogue_style="bilingual",
    )
    assert "MULTILINGUAL / BILINGUAL SHOW DYNAMIC" in prompt
    assert "Each speaker MUST speak in their assigned language" in prompt

def test_episode_create_request_multilingual_fields():
    req = EpisodeCreateRequest(
        topic="Indian Space Tech",
        language="ta-IN",
        dialogue_style="code_mixed",
        speakers=[
            {"speaker_id": "HOST", "display_name": "Host", "voice": "shubh", "pace": 1.0, "language_code": "ta-IN"},
            {"speaker_id": "GUEST", "display_name": "Guest", "voice": "priya", "pace": 1.0, "language_code": "en-IN"},
        ]
    )
    assert req.dialogue_style == "code_mixed"
    assert req.speakers[0].language_code == "ta-IN"
    assert req.speakers[1].language_code == "en-IN"

def test_turn_translate_request_schema():
    req = TurnTranslateRequest(
        text="This is an exciting moment for startups.",
        source_language_code="en-IN",
        target_language_code="hi-IN",
        mode="modern-colloquial"
    )
    assert req.source_language_code == "en-IN"
    assert req.target_language_code == "hi-IN"
    assert req.mode == "modern-colloquial"

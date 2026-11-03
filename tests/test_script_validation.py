import pytest
from app.llm.script_generator import sanitize_turn_text
from app.models.schemas import Outline, OutlineSegment, Script, Segment, Turn

def test_sanitize_turn_text():
    raw = "Hello! [laughter] That's great (laughs) *chuckles* to know."
    cleaned = sanitize_turn_text(raw)
    assert cleaned == "Hello! That's great to know."
    assert "[" not in cleaned and "]" not in cleaned
    assert "(" not in cleaned and ")" not in cleaned

def test_pydantic_script_validation():
    turn1 = Turn(speaker="HOST", text="Welcome to the podcast!", emotion="excited", pause_after_ms=300)
    turn2 = Turn(speaker="GUEST", text="Great to be here!", emotion="happy", pause_after_ms=400)
    seg1 = Segment(name="Intro", summary="Introduction segment", turns=[turn1, turn2])
    script = Script(title="AI Revolution", description="Deep dive into AI", segments=[seg1])

    assert script.title == "AI Revolution"
    assert len(script.segments) == 1
    assert len(script.segments[0].turns) == 2
    assert script.segments[0].turns[0].speaker == "HOST"

def test_pydantic_outline_validation():
    seg = OutlineSegment(title="Origins", goal="Explore founding history", key_points=["point 1", "point 2"])
    outline = Outline(
        title="Sample Show",
        hook="Did you know?",
        intro="Welcome to the show",
        segments=[seg],
        recap="Key takeaways",
        outro="Thanks for listening",
    )
    assert len(outline.segments) == 1
    assert outline.segments[0].key_points == ["point 1", "point 2"]


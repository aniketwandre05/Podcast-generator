import io
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db
from app.research.provider import (
    extract_youtube_video_id,
    is_youtube_url,
    YouTubeResearchProvider,
    summarize_and_build_brief,
)
from app.models.schemas import SourceItem

# Ensure database tables & migrations are in place
init_db()

client = TestClient(app)

# ---------------------------------------------------------
# 1. YouTube URL Detection & Video ID Extraction Tests
# ---------------------------------------------------------
def test_youtube_video_id_extraction():
    test_cases = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120s&feature=share", "dQw4w9WgXcQ"),
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://medium.com/@author/great-post-12345", None),
        ("https://example.com/video/dQw4w9WgXcQ", None),
    ]
    for url, expected_id in test_cases:
        assert extract_youtube_video_id(url) == expected_id

def test_is_youtube_url():
    assert is_youtube_url("https://www.youtube.com/watch?v=12345678901") is True
    assert is_youtube_url("https://youtu.be/12345678901") is True
    assert is_youtube_url("https://news.ycombinator.com") is False
    assert is_youtube_url("not a url") is False

# ---------------------------------------------------------
# 2. Multi-File Document Ingestion Endpoint (/upload-docs)
# ---------------------------------------------------------
def test_multi_document_upload_success():
    txt_content = b"Introduction to Indian AI startup ecosystem and LLM fine-tuning."
    md_content = b"# Hardware Acceleration\nDiscussing TPUs, GPUs, and custom silicon."
    
    files = [
        ("files", ("ecosystem.txt", io.BytesIO(txt_content), "text/plain")),
        ("files", ("hardware.md", io.BytesIO(md_content), "text/markdown")),
    ]
    
    response = client.post("/api/episodes/upload-docs", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["sources"]) == 2
    
    s1, s2 = data["sources"][0], data["sources"][1]
    assert s1["file_type"] == "txt"
    assert s1["title"] == "Ecosystem"
    assert s1["word_count"] > 0
    assert s2["file_type"] == "md"
    assert s2["title"] == "Hardware"
    assert s2["word_count"] > 0

def test_multi_document_upload_unsupported_format():
    files = [
        ("files", ("malware.exe", io.BytesIO(b"binary data"), "application/octet-stream")),
    ]
    response = client.post("/api/episodes/upload-docs", files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]

# ---------------------------------------------------------
# 3. URL Extraction Endpoint (/extract-url) - YouTube & Web
# ---------------------------------------------------------
@patch.object(YouTubeResearchProvider, "extract_info")
def test_extract_url_youtube_success(mock_extract_info):
    mock_extract_info.return_value = {
        "status": "success",
        "source_type": "youtube",
        "video_id": "dQw4w9WgXcQ",
        "title": "Quantum Computing in 2026: Revolutionizing Indian Tech",
        "author": "Tech Bharat Channel",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "content": "Welcome to our deep dive on quantum computing. Today we explore qubits and quantum supremacy.",
        "has_transcript": True,
        "word_count": 16,
    }

    response = client.post(
        "/api/episodes/extract-url",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source_type"] == "youtube"
    assert "Quantum Computing in 2026" in data["title"]
    assert data["author"] == "Tech Bharat Channel"
    assert "Welcome to our deep dive" in data["content"]
    assert data["has_transcript"] is True
    assert data["word_count"] == 16

@patch("app.research.provider.WebUrlResearchProvider.extract_text")
def test_extract_url_webpage_article(mock_extract_text):
    mock_extract_text.return_value = "Title: Sarvam AI Launches Sovereign Indic Models\n\nSarvam AI today announced state-of-the-art multilingual speech synthesis and translation models tailored for 10+ Indian languages."

    response = client.post(
        "/api/episodes/extract-url",
        json={"url": "https://technews.in/sarvam-announcement"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source_type"] == "url"
    assert "Sarvam AI Launches Sovereign Indic Models" in data["title"]
    assert "multilingual speech synthesis" in data["content"]
    assert data["word_count"] > 0

def test_extract_url_invalid_format():
    response = client.post(
        "/api/episodes/extract-url",
        json={"url": "not-a-valid-url"}
    )
    assert response.status_code == 400
    assert "Invalid URL format" in response.json()["detail"]

# ---------------------------------------------------------
# 4. Multi-Source Dossier Synthesis Tests
# ---------------------------------------------------------
@pytest.mark.anyio
@patch("app.research.provider.generate_structured_json")
async def test_summarize_and_build_brief_with_sources(mock_gen_json):
    mock_gen_json.return_value = {
        "key_facts": ["India deep tech growth", "TPUs vs GPUs acceleration"],
        "key_points": ["Cost efficiency in LLMs", "National computing clusters"],
        "interesting_angles": ["Edge AI applications in Indic languages"],
        "sources": ["Lex Fridman Interview", "National AI Strategy Whitepaper"],
    }

    raw_material = "Lex Fridman Interview discussing scaling laws and hardware.\nNational AI Strategy Whitepaper detailing GPU clusters."
    sources = ["Lex Fridman Interview", "National AI Strategy Whitepaper", "Host Talking Points"]

    brief = await summarize_and_build_brief(
        raw_material=raw_material,
        topic="The Future of Indic AI Infrastructure",
        sources=sources,
    )

    # Verify cross-source synthesis contains all sources
    assert "key_facts" in brief
    assert len(brief["key_facts"]) == 2
    assert "Lex Fridman Interview" in brief["sources"]
    assert "National AI Strategy Whitepaper" in brief["sources"]

# ---------------------------------------------------------
# 5. Episode Creation & Storage with Multi-Sources
# ---------------------------------------------------------
@patch("app.api.episodes.run_full_podcast_pipeline")
def test_create_episode_with_multiple_sources(mock_pipeline):
    payload = {
        "topic": "Sovereign AI Stacks in India",
        "source_type": "multi_source",
        "language": "hi-IN",
        "dialogue_style": "code_mixed",
        "tone": "casual",
        "target_duration_mins": 5,
        "speakers": [
            {"speaker_id": "HOST", "display_name": "Shubh", "voice": "shubh", "pace": 1.0, "language_code": "hi-IN"},
            {"speaker_id": "GUEST", "display_name": "Priya", "voice": "priya", "pace": 1.0, "language_code": "hi-IN"}
        ],
        "sources": [
            {
                "id": "yt-001",
                "source_type": "youtube",
                "title": "Deep Tech India Keynote",
                "content": "Transcript of keynote on AI chips and data centers.",
                "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
                "word_count": 9
            },
            {
                "id": "doc-002",
                "source_type": "file",
                "title": "Policy Framework",
                "content": "C:/fake/path/policy.pdf",
                "file_type": "pdf",
                "word_count": 250
            }
        ]
    }

    res = client.post("/api/episodes", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["source_type"] == "multi_source"
    assert len(data["sources"]) == 2
    assert data["sources"][0]["title"] == "Deep Tech India Keynote"
    assert data["sources"][1]["title"] == "Policy Framework"

    # Verify retrieval
    ep_id = data["id"]
    get_res = client.get(f"/api/episodes/{ep_id}")
    assert get_res.status_code == 200
    ep_data = get_res.json()
    assert len(ep_data["sources"]) == 2
    assert ep_data["sources"][0]["source_type"] == "youtube"

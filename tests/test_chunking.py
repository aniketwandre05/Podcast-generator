import pytest
from app.sarvam.tts import chunk_text_by_sentence, compute_tts_cache_key

def test_chunking_under_limit():
    short_text = "This is a brief dialogue sentence that fits well under the limit."
    chunks = chunk_text_by_sentence(short_text, max_chars=100)
    assert len(chunks) == 1
    assert chunks[0] == short_text

def test_chunking_over_limit():
    sentences = [
        "First sentence discussing voice technology in India.",
        "Second sentence providing technical depth and clarity.",
        "Third sentence exploring practical deployment at scale across various sectors.",
        "Fourth sentence concluding the thought nicely.",
    ]
    long_text = " ".join(sentences)
    # Split with small max_chars (e.g. 70)
    chunks = chunk_text_by_sentence(long_text, max_chars=75)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 75

def test_cache_key_deterministic():
    k1 = compute_tts_cache_key("Namaste world", "shubh", "en-IN", 1.0, "bulbul:v3")
    k2 = compute_tts_cache_key("Namaste world", "shubh", "en-IN", 1.0, "bulbul:v3")
    k3 = compute_tts_cache_key("Namaste world", "priya", "en-IN", 1.0, "bulbul:v3")
    assert k1 == k2
    assert k1 != k3


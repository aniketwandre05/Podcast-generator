import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_upload_document_txt():
    content = b"This is a comprehensive research briefing on Quantum Computing breakthroughs in India."
    files = {"file": ("research_notes.txt", io.BytesIO(content), "text/plain")}
    response = client.post("/api/episodes/upload-doc", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["filename"] == "research_notes.txt"
    assert "Quantum Computing" in data["extracted_text"]
    assert data["word_count"] > 0
    assert data["suggested_title"] == "Research Notes"

def test_upload_document_invalid_extension():
    content = b"fake binary exe data"
    files = {"file": ("malicious.exe", io.BytesIO(content), "application/octet-stream")}
    response = client.post("/api/episodes/upload-doc", files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]

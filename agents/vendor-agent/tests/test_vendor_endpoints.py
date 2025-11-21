import pytest
from app import app

@pytest.fixture
def client():
    app.testing = True
    return app.test_client()

def test_create_listing_basic(client, monkeypatch):
    # monkeypatch services to avoid calling real whisper/ollama
    monkeypatch.setattr("services.stt.WhisperCppWrapper.transcribe", lambda self, p: "sample audio transcript")
    monkeypatch.setattr("services.llm.OllamaWrapper.generate", lambda self, p, model=None: "expanded text")
    monkeypatch.setattr("services.llm.OllamaWrapper.embed", lambda self, texts: [[0.1]*384])
    response = client.post("/agent/vendor/create-listing", json={
        "vendor_id": "v1",
        "price": 1000,
        "location": "Pune",
        "media_files": ["tests/sample.wav"],
        "raw_tags": ["rice fields"]
    })
    assert response.status_code == 201
    data = response.json
    assert data["status"] == "ok"

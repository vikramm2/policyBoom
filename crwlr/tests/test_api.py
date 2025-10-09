from fastapi.testclient import TestClient
from app.api import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_endpoint():
    response = client.get("/analyze?url=https://example.com")
    assert response.status_code == 200
    
    data = response.json()
    assert 'seed' in data
    assert 'policy_links' in data
    assert 'results' in data
    assert 'errors' in data
    assert data['seed'] == 'https://example.com'


def test_analyze_with_packs():
    response = client.get("/analyze?url=https://example.com&packs=base")
    assert response.status_code == 200
    
    data = response.json()
    assert 'seed' in data
    assert 'policy_links' in data

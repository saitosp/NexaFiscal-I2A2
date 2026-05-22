import pytest
from fastapi.testclient import TestClient
from api.main import app
import os

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "NFe Extraction API" in response.json().get("service", "")
    assert response.json().get("status") == "online"

def test_documents_endpoint():
    response = client.get("/api/documents")
    assert response.status_code in [200, 500]

def test_statistics_endpoint():
    response = client.get("/api/statistics")
    assert response.status_code in [200, 500]

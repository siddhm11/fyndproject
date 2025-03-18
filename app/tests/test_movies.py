# app/tests/test_movies.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def admin_token():
    # Login as admin and get token
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"]

def test_create_movie_with_admin(admin_token):
    response = client.post(
        "/movies/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Test Movie",
            "description": "A test movie description",
            "release_year": 2023,
            "genre": "Action"
        }
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Test Movie"
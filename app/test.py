import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in str(response.json())

def test_register_user():
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "password": "testpass", "email": "test@example.com"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User registered successfully"

def test_login():
    # First register a test user
    client.post(
        "/auth/register",
        json={"username": "logintest", "password": "testpass", "email": "login@example.com"}
    )
    
    # Then try to login
    response = client.post(
        "/auth/login",
        data={"username": "logintest", "password": "testpass"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_create_movie_without_auth():
    response = client.post(
        "/movies/",
        json={
            "title": "Test Movie",
            "description": "A test movie description",
            "release_year": 2023,
            "genre": "Action"
        }
    )
    assert response.status_code == 401  # Unauthorized
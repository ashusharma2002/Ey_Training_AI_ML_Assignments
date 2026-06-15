import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app


app = create_app()
client = app.test_client()


def test_health():
    response = client.get("/health")

    assert response.status_code == 200


def test_create_prediction():
    response = client.post(
        "/predictions",
        json={
            "text": "hello",
            "confidence": 0.95
        }
    )

    assert response.status_code == 201


def test_invalid_payload():
    response = client.post(
        "/predictions",
        json={
            "wrong": "data"
        }
    )

    assert response.status_code == 422
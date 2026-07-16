"""Tests for the /health endpoint."""

import pytest


def test_health_check_returns_200(client):
    """Health check should return HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_structure(client):
    """Health check response should have expected fields."""
    response = client.get("/health")
    data = response.json()

    assert "status" in data
    assert "app" in data
    assert "version" in data
    assert "db" in data


def test_health_check_db_connected(client):
    """DB should report as connected when in-memory SQLite is available."""
    response = client.get("/health")
    data = response.json()

    assert data["db"] == "connected"
    assert data["status"] == "ok"


def test_health_no_auth_required(client):
    """Health endpoint must be publicly accessible — no auth header needed."""
    # Explicitly omit X-API-Key
    response = client.get("/health", headers={})
    assert response.status_code == 200

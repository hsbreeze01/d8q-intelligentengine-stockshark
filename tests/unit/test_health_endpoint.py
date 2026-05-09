"""Tests for the /api/health endpoint"""

import json
import re

import pytest

from stockshark.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestHealthEndpoint:
    """Spec: GET /api/health returns status ok + UTC ISO 8601 timestamp"""

    def test_returns_200(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_status_is_ok(self, client):
        data = json.loads(client.get("/api/health").data)
        assert data["status"] == "ok"

    def test_timestamp_iso8601_utc(self, client):
        data = json.loads(client.get("/api/health").data)
        ts = data["timestamp"]
        # Should match YYYY-MM-DDTHH:MM:SSZ
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", ts), f"Bad timestamp: {ts}"

    def test_only_status_and_timestamp_keys(self, client):
        data = json.loads(client.get("/api/health").data)
        assert set(data.keys()) == {"status", "timestamp"}

    def test_no_auth_required(self, client):
        """Health endpoint is accessible without any authentication headers."""
        resp = client.get("/api/health")
        assert resp.status_code == 200

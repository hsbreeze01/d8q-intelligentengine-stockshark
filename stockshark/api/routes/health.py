"""Health check API 路由"""

from datetime import datetime, timezone

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("", methods=["GET"])
def health_check():
    """GET /api/health — returns status and server-generated UTC timestamp"""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return jsonify({"status": "ok", "timestamp": ts}), 200

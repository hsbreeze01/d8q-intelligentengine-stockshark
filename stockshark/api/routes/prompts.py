"""Shark Prompt 管理 API"""
import os
import sys
from flask import Blueprint, request, jsonify

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from prompt_loader import PromptManager

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'prompts')
pm = PromptManager(PROMPTS_DIR)

prompts_bp = Blueprint('prompts', __name__)


@prompts_bp.route('/', methods=['GET'])
def list_prompts():
    """列出所有 Prompt 配置"""
    return jsonify({"success": True, "prompts": pm.list_all(), "service": "shark"})


@prompts_bp.route('/<path:prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    """获取单个 Prompt 配置"""
    p = pm.get(prompt_id)
    if p:
        return jsonify({"success": True, "prompt": p})
    return jsonify({"success": False, "error": "Prompt not found"}), 404


@prompts_bp.route('/<path:prompt_id>', methods=['PUT'])
def update_prompt(prompt_id):
    """更新 Prompt 配置"""
    body = request.json or {}
    if pm.save(prompt_id, body):
        return jsonify({"success": True, "message": "Prompt updated"})
    return jsonify({"success": False, "error": "Save failed"}), 500

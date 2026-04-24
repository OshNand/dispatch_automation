import json
import logging
import re
from .llm_client import query_llm
from tools.file_ops import list_files

logger = logging.getLogger(__name__)

def translate_prompt_to_sessions(master_prompt: str) -> list:
    """
    Translates a master prompt into a structured list of sessions using the LLM.
    Handles JSON parsing robustly with multiple fallback strategies.
    """
    try:
        repo_context = list_files()
    except Exception as e:
        logger.warning(f"Failed to get repo context: {e}")
        repo_context = "[Repo context unavailable]"
    
    prompt = f"""You are an expert technical lead and software architect.
A user has provided a master prompt to modify or create a project.
Here is the repository structure:
{repo_context}

Master Prompt:
{master_prompt}

Your task is to break down this prompt into a sequential list of atomic development sessions.
Each session MUST follow this exact JSON structure:
{{
  "id": integer,
  "goal": "string describing what to achieve in this session",
  "targets": ["list", "of", "file", "paths"],
  "type": "read" or "edit" or "test",
  "depends_on": []
}}

IMPORTANT RULES:
- Output ONLY a valid JSON array of sessions
- Max 3-5 files per session
- No markdown, no explanations, only JSON"""

    response_text = query_llm(prompt, json_format=True)
    sessions = _parse_json_response(response_text)
    
    if not sessions:
        logger.error(f"Failed to parse sessions: {response_text[:100]}")
        return [{"id": 1, "goal": "Review prompt", "targets": [], "type": "read", "depends_on": []}]
    
    logger.info(f"Generated {len(sessions)} sessions")
    return sessions

def _parse_json_response(response_text: str) -> list:
    """Multiple fallback strategies for JSON parsing."""
    if not response_text:
        return []
    
    response_text = response_text.strip()
    
    # Strategy 1: Direct parse
    try:
        data = json.loads(response_text)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "sessions" in data:
            return data.get("sessions", []) if isinstance(data.get("sessions"), list) else []
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Remove markdown code blocks
    try:
        cleaned = response_text.strip()
        if "```" in cleaned:
            cleaned = re.sub(r'```(?:json)?\s*', '', cleaned)
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "sessions" in data:
            return data.get("sessions", [])
    except json.JSONDecodeError:
        pass
    
    # Strategy 3: Extract JSON array
    try:
        match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, AttributeError):
        pass
    
    logger.warning(f"JSON parsing failed, trying fallback")
    return []

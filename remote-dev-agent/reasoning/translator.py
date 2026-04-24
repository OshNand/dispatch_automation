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
    logger.debug(f"Raw LLM response: {response_text}")
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
    
    def normalize_data(data):
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Case 1: Wrapped in "sessions" key
            if "sessions" in data and isinstance(data["sessions"], list):
                return data["sessions"]
            # Case 2: Single session object
            if "goal" in data and "id" in data:
                return [data]
        return []

    # Strategy 1: Direct parse
    try:
        data = json.loads(response_text)
        result = normalize_data(data)
        if result: return result
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract from markdown code blocks
    try:
        matches = re.findall(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
        for match in matches:
            try:
                data = json.loads(match)
                result = normalize_data(data)
                if result: return result
            except json.JSONDecodeError:
                continue
    except Exception:
        pass
    
    # Strategy 3: Extract first JSON array or object
    try:
        # Try array first
        array_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if array_match:
            try:
                data = json.loads(array_match.group(0))
                if isinstance(data, list): return data
            except json.JSONDecodeError:
                pass
        
        # Try object
        obj_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if obj_match:
            try:
                data = json.loads(obj_match.group(0))
                result = normalize_data(data)
                if result: return result
            except json.JSONDecodeError:
                pass
    except Exception:
        pass
    
    logger.warning(f"JSON parsing failed for response: {response_text[:200]}...")
    return []

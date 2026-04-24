import json
import logging
from .llm_client import query_llm
from tools.file_ops import list_files

logger = logging.getLogger(__name__)

def translate_prompt_to_sessions(master_prompt: str) -> list[dict]:
    """
    Translates a master prompt into a structured list of sessions using the LLM.
    """
    repo_context = list_files()
    
    prompt = f"""
You are an expert technical lead and software architect.
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
  "type": "read" | "edit" | "test",
  "depends_on": [list of prerequisite session ids]
}}

Constraints:
- Max 3-5 files per session.
- Output ONLY a valid JSON array of session objects.
- Do not output any markdown formatting, just the raw JSON.
"""

    response_text = query_llm(prompt, json_format=True)
    
    try:
        # Try parsing directly
        sessions = json.loads(response_text)
        if isinstance(sessions, dict) and "sessions" in sessions:
            sessions = sessions["sessions"]
        return sessions if isinstance(sessions, list) else []
    except json.JSONDecodeError:
        logger.error(f"Failed to parse translator output as JSON: {response_text}")
        # Very basic fallback/cleanup if Ollama wrapped it in markdown
        cleaned = response_text.strip().removeprefix("```json").removesuffix("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return [{"id": 1, "goal": "Error parsing sessions. Please review master prompt.", "targets": [], "type": "read", "depends_on": []}]

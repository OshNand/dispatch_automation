import json
import logging
import re
from .llm_client import query_llm
from tools.file_ops import read_file

logger = logging.getLogger(__name__)

def generate_session_plan(session: dict) -> dict:
    """
    Takes a specific session and generates actionable steps using the LLM.
    Returns a dictionary of steps with robust error handling.
    """
    # Gather content of target files if type is 'edit' or 'test'
    files_context = ""
    if session.get("type") in ["edit", "test"]:
        for file_path in session.get("targets", []):
            try:
                content = read_file(file_path)
                # Limit file content to 5000 characters
                if len(content) > 5000:
                    content = content[:5000] + "\n... [truncated]"
                files_context += f"\n--- {file_path} ---\n{content}\n"
            except FileNotFoundError:
                files_context += f"\n--- {file_path} ---\n(File does not exist yet)\n"
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
                files_context += f"\n--- {file_path} ---\n(Could not read: {str(e)})\n"

    prompt = f"""You are an autonomous AI coding agent executing a development task.

Session Goal: {session.get("goal")}
Session Type: {session.get("type")}
Target Files: {session.get("targets")}

Current file contents:
{files_context}

Generate a plan of executable steps. Return ONLY valid JSON:
{{
    "steps": [
        {{
            "action": "read_file" or "write_file" or "run_command",
            "path": "file path if applicable",
            "content": "content if write_file",
            "command": "command if run_command"
        }}
    ]
}}

Rules:
- Only output JSON, no markdown or explanations
- Action must be one of: read_file, write_file, run_command
- Keep steps simple and atomic"""

    response_text = query_llm(prompt, json_format=True)
    plan = _parse_plan_json(response_text)
    
    if not plan.get("steps"):
        logger.warning("Planner generated no steps")
    
    logger.info(f"Generated plan with {len(plan.get('steps', []))} steps")
    return plan

def _parse_plan_json(response_text: str) -> dict:
    """Parse JSON plan with multiple fallback strategies."""
    if not response_text:
        return {"steps": []}
    
    response_text = response_text.strip()
    
    # Strategy 1: Direct parse
    try:
        data = json.loads(response_text)
        if isinstance(data, dict) and "steps" in data:
            return data
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Remove markdown code blocks
    try:
        cleaned = response_text.strip()
        if "```" in cleaned:
            cleaned = re.sub(r'```(?:json)?\s*', '', cleaned)
        data = json.loads(cleaned)
        if isinstance(data, dict) and "steps" in data:
            return data
    except json.JSONDecodeError:
        pass
    
    # Strategy 3: Extract JSON object
    try:
        match = re.search(r'{.*"steps".*}', response_text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            if isinstance(data, dict) and "steps" in data:
                return data
    except (json.JSONDecodeError, AttributeError):
        pass
    
    logger.warning(f"All plan parsing strategies failed")
    return {"steps": []}

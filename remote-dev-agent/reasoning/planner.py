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

    prompt = f"""You are an autonomous AI coding agent.
Session Goal: {session.get("goal")}
Session Type: {session.get("type")}
Target Files: {session.get("targets")}

Current file contents:
{files_context}

Output ONLY a valid JSON object with the following structure:
{{
    "steps": [
        {{
            "action": "read_file" | "write_file" | "run_command",
            "path": "path",
            "content": "content",
            "command": "command"
        }}
    ]
}}
Rules: No markdown, no explanations, only valid JSON."""

    response_text = query_llm(prompt, json_format=True)
    logger.debug(f"Raw LLM plan response: {response_text}")
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
    
    def normalize_plan(data):
        if isinstance(data, dict) and "steps" in data:
            return data
        if isinstance(data, list):
            return {"steps": data}
        return None

    # Strategy 1: Direct parse
    try:
        data = json.loads(response_text)
        result = normalize_plan(data)
        if result: return result
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract from markdown code blocks
    try:
        matches = re.findall(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
        for match in matches:
            try:
                data = json.loads(match)
                result = normalize_plan(data)
                if result: return result
            except json.JSONDecodeError:
                continue
    except Exception:
        pass
    
    # Strategy 3: Extract JSON object or array
    try:
        # Try object first
        obj_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if obj_match:
            try:
                data = json.loads(obj_match.group(0))
                result = normalize_plan(data)
                if result: return result
            except json.JSONDecodeError:
                pass
        
        # Try array
        array_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if array_match:
            try:
                data = json.loads(array_match.group(0))
                if isinstance(data, list): return {"steps": data}
            except json.JSONDecodeError:
                pass
    except Exception:
        pass
    
    logger.warning(f"All plan parsing strategies failed")
    return {"steps": []}

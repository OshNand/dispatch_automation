import json
import logging
from .llm_client import query_llm
from tools.file_ops import read_file

logger = logging.getLogger(__name__)

def generate_session_plan(session: dict) -> dict:
    """
    Takes a specific session and generates actionable steps using the LLM.
    Returns a dictionary of steps.
    """
    # Gather content of target files if type is 'edit' or 'test'
    files_context = ""
    if session.get("type") in ["edit", "test"]:
        for file_path in session.get("targets", []):
            try:
                content = read_file(file_path)
                files_context += f"\n--- {file_path} ---\n{content}\n"
            except FileNotFoundError:
                files_context += f"\n--- {file_path} ---\n(File does not exist yet)\n"

    prompt = f"""
You are an autonomous AI coding agent.
Your current session goal is: {session.get("goal")}
Session Type: {session.get("type")}
Target Files: {session.get("targets")}

Here is the current content of the target files:
{files_context}

Create a structured plan of execution for this session.
Return ONLY a valid JSON object matching this structure:
{{
    "steps": [
        {{
            "action": "write_file" | "run_command" | "read_file",
            "path": "file_path_if_applicable",
            "content": "file_content_if_write_file",
            "command": "command_string_if_run_command"
        }}
    ]
}}
Do NOT output anything other than the JSON object. No markdown, no explanations.
"""

    response_text = query_llm(prompt, json_format=True)
    
    try:
        plan = json.loads(response_text)
        return plan
    except json.JSONDecodeError:
        logger.error(f"Failed to parse planner output as JSON: {response_text}")
        cleaned = response_text.strip().removeprefix("```json").removesuffix("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"steps": []}

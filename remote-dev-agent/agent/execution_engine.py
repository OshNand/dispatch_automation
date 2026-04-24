import logging
from reasoning.planner import generate_session_plan
from tools.file_ops import write_file, read_file
from tools.cmd_ops import run_command
from monitor.safety_controller import safety_controller

logger = logging.getLogger(__name__)

def execute_session(session: dict, safety_callback=None) -> dict:
    """
    Executes a single session safely.
    Returns a session report.
    """
    session_id = session.get("id")
    goal = session.get("goal")
    
    report = {
        "session_id": session_id,
        "goal": goal,
        "changes": [],
        "status": "failed",
        "notes": ""
    }

    try:
        # 1. Enforce Safety
        safety_controller.enforce_safety(callback=safety_callback)

        # 2. Plan steps
        plan = generate_session_plan(session)
        steps = plan.get("steps", [])
        
        if not steps:
            report["notes"] = "Planner generated no steps."
            return report

        # 3. Execute steps
        for step in steps:
            # Enforce safety between steps
            safety_controller.enforce_safety(callback=safety_callback)
            
            action = step.get("action")
            if action == "write_file":
                path = step.get("path")
                content = step.get("content")
                if path and content:
                    write_file(path, content)
                    report["changes"].append(f"Wrote file: {path}")
            elif action == "read_file":
                path = step.get("path")
                if path:
                    # Reading just loads it into context or verifies existence
                    try:
                        read_file(path)
                        report["changes"].append(f"Read file: {path}")
                    except FileNotFoundError:
                        report["changes"].append(f"Attempted to read non-existent file: {path}")
            elif action == "run_command":
                command = step.get("command")
                if command:
                    out = run_command(command)
                    report["changes"].append(f"Ran command: {command} (Output length: {len(out)})")

        report["status"] = "success"
        report["notes"] = "Session executed successfully."

    except Exception as e:
        logger.error(f"Error executing session {session_id}: {str(e)}")
        report["notes"] = f"Error during execution: {str(e)}"
        
    return report

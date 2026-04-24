# Remote Autonomous Development Agent

A complete **LOCAL-FIRST autonomous development agent** that takes natural language prompts via Telegram, breaks them into structured sessions, and executes them safely with real-time system monitoring and user approval workflows.

## 🎯 Key Features

✅ **Telegram Interface** - Send development tasks via natural language prompts
✅ **Session-Based Execution** - Automatic breakdown into atomic development sessions
✅ **User Approval Workflow** - Each session requires user approval before execution
✅ **System Monitoring** - Real-time CPU, RAM, GPU, and temperature tracking
✅ **Safety Control** - Automatic pause/cooldown when system resources exceed thresholds
✅ **Error Recovery** - Checkpoints and retry logic for resilient execution
✅ **Comprehensive Logging** - Detailed execution logs for every session
✅ **Security Validation** - File path validation, command sanitization
✅ **Local LLM** - Uses Ollama (Gemma E4B) - no cloud dependencies
✅ **No Auto-Push** - Manual review before git push (you control the workflow)

## 🏗️ Architecture

```
remote-dev-agent/
├── bot/                    # Telegram bot interface & handlers
├── agent/                  # Session execution engine
├── reasoning/              # LLM-based prompt translation & planning
├── monitor/                # System monitoring & safety controller
├── tools/                  # Safe file/command/git operations
├── utils/                  # Session mgmt, logging, validation
├── config/                 # Configuration & settings
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 📋 Prerequisites

- **Python 3.10+** installed
- **Ollama** installed locally ([https://ollama.ai](https://ollama.ai))
- **Gemma E4B** model pulled in Ollama
- **Telegram Bot Token** from @BotFather
- **Numeric Telegram User ID** (from @userinfobot or startup logs)
- **Git** installed
- **Windows/Linux/macOS** with 16GB+ RAM

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```powershell
# Windows PowerShell
$env:TELEGRAM_BOT_TOKEN = "your_bot_token_here"
$env:ALLOWED_USER_ID = "your_numeric_user_id"
$env:OLLAMA_BASE_URL = "http://localhost:11434/api"
$env:OLLAMA_MODEL = "gemma"
```

Or set them permanently:
```powershell
[Environment]::SetEnvironmentVariable("TELEGRAM_BOT_TOKEN", "your_token", "User")
[Environment]::SetEnvironmentVariable("ALLOWED_USER_ID", "your_id", "User")
```

### 3. Ensure Ollama is Running

```bash
# In a separate terminal
ollama serve

# In another terminal (verify Gemma is downloaded)
ollama pull gemma
```

### 4. Create Workspace Directory

```bash
mkdir "C:\Users\oshna\Desktop\REMOTE WORKSPACE"
```

### 5. Start the Agent

```bash
python main.py
```

## 💬 Usage

### Start the Bot

1. Open Telegram and find your bot (or search for its username)
2. Send `/start` to verify connection
3. Send `/status` to see system metrics

### Send a Master Prompt

Send any development task description, for example:

```
Create a Python REST API with FastAPI that has:
- Health check endpoint
- User CRUD operations
- SQLite database
- Environment variables support
```

### The Workflow

1. **LLM Analysis**: System uses Gemma to break down your prompt into sessions
2. **Session Presentation**: Each session is presented to you with approval buttons
3. **User Approval**: Click YES to execute, SKIP to skip, or STOP to abort
4. **Execution**: System executes the session with safety checks
5. **Monitoring**: Real-time CPU/GPU/Temp monitoring during execution
6. **Report**: Detailed report sent after each session
7. **Safety**: If system overload detected, automatic pause and cooldown
8. **Final Report**: Summary of all completed sessions

### Commands

- `/start` - Initialize bot
- `/status` - Show current system metrics
- Any text message - Send as master prompt

### Response Buttons

- **YES** - Execute session
- **SKIP** - Skip this session
- **STOP** - Abort workflow
- **RETRY** - Retry failed session (appears on errors)
- **MODIFY** - Modify next session (admin use)

## 🔧 System Configuration

Edit `config/settings.py` or use environment variables:

```python
# Safety Thresholds
CPU_CRITICAL_PERCENT = 95.0      # CPU safety limit
GPU_CRITICAL_PERCENT = 95.0      # GPU safety limit
TEMP_CRITICAL_C = 85.0           # Temperature safety limit
COOLDOWN_SECONDS = 600           # Cooldown period (10 min)

# Execution
SESSION_TIMEOUT_SECONDS = 300    # Max time per session (5 min)
MAX_FILE_SIZE_MB = 50.0          # Max file size to process
MAX_FILES_PER_SESSION = 5        # Max files per session
```

## 📁 File Locations

- **Workspace**: `C:\Users\oshna\Desktop\REMOTE WORKSPACE`
- **Logs**: `logs/` - Detailed execution logs
- **Tasks**: `tasks/` - Session queue files
- **Checkpoints**: `checkpoints/` - Recovery data

## 🛡️ Security Features

✅ **Path Validation** - All file paths validated against workspace directory
✅ **Command Sanitization** - Dangerous commands blocked (rm -rf, mkfs, dd, etc.)
✅ **File Size Limits** - Max 50MB files to prevent memory issues
✅ **User Authorization** - Only authorized Telegram users can execute
✅ **Step Validation** - Each execution step validated before running
✅ **Safe File Operations** - No absolute paths, no shell injection

## 🧠 Reasoning Pipeline

### Phase 1: Prompt Translation
- Master prompt sent to LLM (Gemma via Ollama)
- LLM breaks down into structured JSON sessions
- Robust JSON parsing with multiple fallback strategies

### Phase 2: Session Planning
- Each session passed to LLM for detailed planning
- Generates atomic steps: read_file, write_file, run_command
- Validation before execution

### Phase 3: Safe Execution
- Checkpoints saved after each step
- Real-time safety monitoring
- Automatic recovery from failures
- Detailed logging of all operations

## 📊 Safety States

```
RUNNING → WARNING (>80%) → CRITICAL (>95%) → PAUSED → COOLDOWN → RESUMING
```

When system enters CRITICAL state:
1. Current execution is paused safely
2. Checkpoint is saved
3. User notified via Telegram
4. Adaptive cooldown timer starts (10-30 min)
5. After cooldown, execution resumes from checkpoint

## 📝 Execution Logs

Each session execution is logged to `logs/session_<id>_<timestamp>.json`:

```json
{
  "session_id": 1,
  "goal": "Create API endpoints",
  "status": "success",
  "steps": [...],
  "start_time": "2026-04-24T10:30:00",
  "end_time": "2026-04-24T10:35:00",
  "warnings": []
}
```

## 🔄 Checkpoint & Recovery

The system automatically saves checkpoints:
- After each successful step
- Before entering cooldown
- Allows recovery if execution is interrupted

Load checkpoints:
- Automatically on session retry
- Resumes from last successful step
- Clears checkpoint on successful completion

## ❌ Error Handling

On step failure:
1. Logs error details
2. Attempts automatic retry (up to 3 times)
3. If retry fails, prompts user: RETRY / SKIP / STOP
4. Continues with next session if SKIP selected

## 🎮 Hardware Requirements

Tested on:
- **CPU**: Modern multi-core (Intel/AMD)
- **RAM**: 16GB minimum, 32GB recommended
- **GPU**: RTX 3050 (4GB VRAM) or similar, CPU fallback supported
- **Storage**: SSD recommended, 50GB+ free space
- **Network**: Local LLM only, no internet required for execution

## 🐛 Troubleshooting

### Bot doesn't respond
- Check TELEGRAM_BOT_TOKEN is set correctly
- Verify internet connection (for Telegram only)
- Check logs for errors: `python main.py`

### LLM not responding
- Ensure Ollama is running: `ollama serve`
- Verify Gemma is pulled: `ollama list`
- Check OLLAMA_BASE_URL is correct
- Try simple prompt first

### High system load
- Check background processes
- Increase COOLDOWN_SECONDS in config
- Reduce MAX_FILE_SIZE_MB
- Ensure GPU isn't already in use

### Sessions fail
- Check workspace directory exists
- Verify permissions for workspace
- Review logs in `logs/` directory
- Check target files exist

## 📈 Workflow Example

```
User: "Create a Python web scraper"
          ↓
Agent: Generates 3 sessions
  Session 1: [Setup] - read requirements, create env
  Session 2: [Code] - write scraper.py, tests
  Session 3: [Test] - run tests, verify output
          ↓
User: Approves Session 1
  → Executes (2 steps, 30 sec)
  → Checkpoint saved ✓
  → Report sent
          ↓
User: Approves Session 2
  → Executes (4 steps, 1 min 20 sec)
  → Temp warning: 78°C (caution)
  → Checkpoint saved ✓
  → Report sent
          ↓
User: Approves Session 3
  → Executes (2 steps, 45 sec)
  → All tests pass ✓
  → Checkpoint cleared
          ↓
Final Report: 3/3 successful
Workspace ready for review → Manual git push
```

## 🔐 Important Notes

⚠️ **NO AUTOMATIC GIT PUSH** - You must review and push manually
⚠️ **LOCAL ONLY** - No cloud services, all processing local
⚠️ **USER APPROVAL REQUIRED** - Every session needs your OK
⚠️ **WORKSPACE CRITICAL** - Ensure workspace is backed up
⚠️ **OLLAMA REQUIRED** - System won't work without local LLM

## 📚 Additional Resources

- [Ollama Documentation](https://ollama.ai)
- [Gemma Model](https://ai.google.dev/tutorials/gemma_pytorch)
- [python-telegram-bot Docs](https://python-telegram-bot.readthedocs.io)
- [Pydantic Documentation](https://docs.pydantic.dev)

## 🤝 Contributing

This is a personal local-first agent. Modify `config/settings.py` for customization.

## 📄 License

Local use only. Modify for your needs.

## 🎯 v1 Status

✅ Core execution engine complete
✅ Telegram bot with approval workflow
✅ Safety monitoring & cooldown
✅ Checkpoint & recovery system
✅ Comprehensive logging
✅ Security validation
✅ Error handling & retry logic
✅ Final report generation

Ready for production use! 🚀
7. Repeat until all sessions are complete.
8. Send `/status` anytime to check your PC's telemetry (CPU, RAM, GPU, Temp).

## Safety & Security

- **User Validation**: Only responds to `ALLOWED_USER_ID`.
- **Sandbox Context**: File operations are bounded to the `workspace/` directory within this project.
- **Thermal & Load Throttling**: Auto-pauses if system hits 95% CPU/GPU or 85°C.

import logging
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config.settings import settings
from monitor.system_monitor import format_system_status
from reasoning.translator import translate_prompt_to_sessions
from agent.execution_engine import executor
from utils import execution_logger

logger = logging.getLogger(__name__)

# Global state to track sessions
app_state = {
    "sessions": [],
    "current_session_index": 0,
    "completed_sessions": [],
    "paused": False,
    "user_context": None,
    "failed_sessions": []
}

def is_allowed(update: Update) -> bool:
    """Checks if the user is authorized."""
    user_id = str(update.effective_user.id)
    return user_id == settings.ALLOWED_USER_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("Unauthorized user.")
        return
    await update.message.reply_text("🤖 Remote Autonomous Dev Agent online. Send me a master prompt to begin.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    status_msg = format_system_status()
    await update.message.reply_text(status_msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    
    prompt = update.message.text
    await update.message.reply_text("🧠 Analyzing master prompt and building sessions... (This may take a minute)")
    
    # Run translator
    sessions = translate_prompt_to_sessions(prompt)
    
    if not sessions:
        await update.message.reply_text("Failed to generate sessions or no tasks found. Please try rephrasing.")
        return
        
    app_state["sessions"] = sessions
    app_state["current_session_index"] = 0
    app_state["completed_sessions"] = []
    
    summary = f"Generated {len(sessions)} sessions.\n"
    for s in sessions:
        summary += f"- [{s.get('id')}] {s.get('goal')} ({s.get('type')})\n"
        
    await update.message.reply_text(summary)
    await prompt_next_session(update, context)

async def prompt_next_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if app_state["current_session_index"] >= len(app_state["sessions"]):
        await send_final_report(update, context)
        return
        
    session = app_state["sessions"][app_state["current_session_index"]]
    
    text = f"🎯 **Next Session [{session.get('id')}]**\n"
    text += f"**Goal**: {session.get('goal')}\n"
    text += f"**Targets**: {', '.join(session.get('targets', []))}\n"
    text += "\nProceed?"
    
    keyboard = [
        [
            InlineKeyboardButton("YES", callback_data="proceed_yes"),
            InlineKeyboardButton("SKIP", callback_data="proceed_skip"),
            InlineKeyboardButton("STOP", callback_data="proceed_stop")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses for session approval/skip/stop."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "proceed_stop":
        await query.edit_message_text(text="🛑 Execution stopped by user. Review completed sessions below.")
        await send_final_report(update, context)
        return
    
    if data == "proceed_skip":
        session = app_state["sessions"][app_state["current_session_index"]]
        app_state["current_session_index"] += 1
        await query.edit_message_text(text=f"⏭️ Session {session.get('id')} skipped.")
        await prompt_next_session(update, context)
        return
    
    if data == "proceed_yes":
        session = app_state["sessions"][app_state["current_session_index"]]
        session_id = session.get("id")
        
        await query.edit_message_text(text=f"⚙️ Executing Session {session_id}... (This may take a while)")
        
        try:
            # Create a callback for safety alerts during execution
            safety_messages = []
            def safety_alert(msg):
                safety_messages.append(msg)
                logger.warning(f"SAFETY ALERT: {msg}")
            
            # Execute the session with error handling and retry support
            report = executor.execute_session(session, safety_callback=safety_alert)
            
            # Store completed session
            app_state["completed_sessions"].append(report)
            
            # Send detailed report
            await send_session_report(query, report, safety_messages)
            
            # Move to next session
            app_state["current_session_index"] += 1
            await prompt_next_session(update, context)
            
        except Exception as e:
            logger.error(f"Error executing session {session_id}: {e}", exc_info=True)
            
            # Store failed session
            failed_report = {
                "session_id": session_id,
                "goal": session.get("goal"),
                "status": "error",
                "error": str(e),
                "changes": []
            }
            app_state["failed_sessions"].append(failed_report)
            app_state["completed_sessions"].append(failed_report)
            
            # Ask user for action
            error_msg = f"❌ Session {session_id} encountered an error: {str(e)[:100]}\n\nWhat would you like to do?"
            keyboard = [
                [
                    InlineKeyboardButton("RETRY", callback_data=f"retry_{session_id}"),
                    InlineKeyboardButton("SKIP", callback_data="proceed_skip"),
                    InlineKeyboardButton("STOP", callback_data="proceed_stop")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(error_msg, reply_markup=reply_markup)
    
    # Retry logic
    if data.startswith("retry_"):
        session = app_state["sessions"][app_state["current_session_index"]]
        session_id = session.get("id")
        
        await query.edit_message_text(text=f"🔄 Retrying Session {session_id}...")
        
        try:
            safety_messages = []
            def safety_alert(msg):
                safety_messages.append(msg)
            
            report = executor.execute_session(session, safety_callback=safety_alert, retry_on_failure=True)
            app_state["completed_sessions"].append(report)
            
            await send_session_report(query, report, safety_messages)
            
            app_state["current_session_index"] += 1
            await prompt_next_session(update, context)
            
        except Exception as e:
            await query.message.reply_text(f"❌ Retry failed: {str(e)[:100]}")

async def send_session_report(query, report: dict, safety_messages: list = None):
    """Send detailed session execution report."""
    status_emoji = "✅" if report["status"] == "success" else "❌"
    
    report_text = f"{status_emoji} **Session {report['session_id']} Report**\n"
    report_text += f"Goal: {report['goal']}\n"
    report_text += f"Status: {report['status'].upper()}\n"
    report_text += f"Notes: {report.get('notes', 'N/A')}\n\n"
    
    if report["changes"]:
        report_text += "**Changes:**\n"
        for change in report["changes"][:10]:  # Limit to first 10 changes
            report_text += f"  {change}\n"
        if len(report["changes"]) > 10:
            report_text += f"  ... and {len(report['changes']) - 10} more\n"
    
    if safety_messages:
        report_text += "\n⚠️ **Safety Alerts:**\n"
        for msg in safety_messages[:5]:
            report_text += f"  • {msg}\n"
    
    if report.get("retry_count"):
        report_text += f"\n🔄 Retries: {report['retry_count']}\n"
    
    await query.message.reply_text(report_text, parse_mode="Markdown")

async def send_final_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send comprehensive final execution report."""
    total = len(app_state["sessions"])
    completed = len(app_state["completed_sessions"])
    success = sum(1 for r in app_state["completed_sessions"] if r["status"] == "success")
    failed = len(app_state["failed_sessions"])
    skipped = total - completed
    
    # Get execution summary from logger
    exec_summary = execution_logger.generate_execution_summary()
    
    report = "📈 **FINAL EXECUTION REPORT**\n\n"
    report += f"**Summary:**\n"
    report += f"  Total Sessions: {total}\n"
    report += f"  ✅ Successful: {success}\n"
    report += f"  ❌ Failed: {failed}\n"
    report += f"  ⏭️ Skipped: {skipped}\n"
    report += f"  ⚙️ Executed: {completed}\n\n"
    
    if app_state["completed_sessions"]:
        report += "**Completed Sessions:**\n"
        for session_report in app_state["completed_sessions"][:10]:
            status = "✅" if session_report["status"] == "success" else "❌"
            report += f"  {status} [{session_report['session_id']}] {session_report['goal'][:50]}\n"
    
    if failed > 0:
        report += f"\n⚠️ **{failed} Session(s) Failed**\n"
        if app_state["failed_sessions"]:
            for failed_session in app_state["failed_sessions"][:3]:
                report += f"  • Session {failed_session['session_id']}: {failed_session.get('error', 'Unknown error')[:50]}\n"
    
    report += "\n" + "="*50 + "\n"
    report += "✅ **All tasks completed!**\n\n"
    report += "📋 **Next Steps:**\n"
    report += "  1. Review changes in your workspace\n"
    report += "  2. Test the modifications\n"
    report += "  3. Commit changes manually (no auto-push)\n"
    report += "  4. Push to GitHub when ready\n\n"
    report += "📁 Workspace: `C:\\\\Users\\\\oshna\\\\Desktop\\\\REMOTE WORKSPACE`\n"
    report += "📊 Logs: Check `logs/` directory for detailed execution logs\n"
    
    if update.message:
        await update.message.reply_text(report, parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text(report, parse_mode="Markdown")

def run_bot():
    token = settings.TELEGRAM_BOT_TOKEN
    if token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error("Please set TELEGRAM_BOT_TOKEN in config or environment variables.")
        return
        
    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("Starting Telegram Bot...")
    application.run_polling()

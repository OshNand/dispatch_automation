import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config.settings import settings
from monitor.system_monitor import format_system_status
from reasoning.translator import translate_prompt_to_sessions
from agent.execution_engine import execute_session

logger = logging.getLogger(__name__)

# Global state to track sessions
app_state = {
    "sessions": [],
    "current_session_index": 0,
    "completed_sessions": []
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
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "proceed_stop":
        await query.edit_message_text(text="🛑 Execution stopped by user.")
        return
        
    if data == "proceed_skip":
        app_state["current_session_index"] += 1
        await query.edit_message_text(text="⏭️ Session skipped.")
        await prompt_next_session(update, context)
        return
        
    if data == "proceed_yes":
        session = app_state["sessions"][app_state["current_session_index"]]
        await query.edit_message_text(text=f"⚙️ Executing Session {session.get('id')}...")
        
        # Async wrapper to send safety alerts if they happen during execution
        def safety_alert(msg):
            # This is synchronous but called from sync code. 
            # In a full async app, we'd use a queue. For now, logging will catch it.
            logger.warning(msg)
            
        report = execute_session(session, safety_callback=safety_alert)
        app_state["completed_sessions"].append(report)
        
        report_text = f"📊 **Session {report['session_id']} Report**\n"
        report_text += f"Status: {report['status']}\n"
        report_text += f"Notes: {report['notes']}\n"
        report_text += "Changes:\n" + "\n".join([f"- {c}" for c in report['changes']])
        
        await query.message.reply_text(report_text, parse_mode="Markdown")
        
        app_state["current_session_index"] += 1
        await prompt_next_session(update, context)

async def send_final_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = len(app_state["sessions"])
    success = sum(1 for r in app_state["completed_sessions"] if r["status"] == "success")
    
    report = "📈 **FINAL EXECUTION REPORT**\n\n"
    report += f"Total Sessions: {total}\n"
    report += f"Successful: {success}\n"
    report += f"Failed/Skipped: {total - success}\n\n"
    report += "All tasks completed. Check your workspace and review before git push."
    
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

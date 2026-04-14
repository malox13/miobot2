from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_activities, get_activity_completion_rate, get_period_key

MAIN_MENU = 0

TIMEFRAME_EMOJI = {"daily": "📅", "weekly": "📆", "monthly": "🗓️"}
TIMEFRAME_LABEL = {"daily": "Oggi", "weekly": "Questa settimana", "monthly": "Questo mese"}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data.clear()
    await show_main_menu(update, context, user_id)
    return MAIN_MENU

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int = None):
    if user_id is None:
        user_id = update.effective_user.id

    activities = get_activities(user_id)
    keyboard = []

    for act in activities:
        period_key = get_period_key(act["timeframe"])
        comp, total = get_activity_completion_rate(act["id"], user_id, period_key)
        tf_emoji = TIMEFRAME_EMOJI.get(act["timeframe"], "📅")

        if total == 0:
            status = "⬜"
        elif comp == total:
            status = "✅"
        elif comp > 0:
            status = "🟨"
        else:
            status = "⬜"

        label = f"{status} {act['name']} ({comp}/{total}) {tf_emoji}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"activity:{act['id']}")])

    keyboard.append([InlineKeyboardButton("➕ Nuova attività", callback_data="new_activity")])
    keyboard.append([InlineKeyboardButton("📊 Statistiche globali", callback_data="global_stats")])

    text = (
        "🏠 *Menu principale*\n\n"
        "Ecco le tue abitudini di oggi.\n"
        "Toccane una per aggiornarla, o creane una nuova."
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text, reply_markup=reply_markup, parse_mode="Markdown"
            )
        except Exception:
            await update.callback_query.message.reply_text(
                text, reply_markup=reply_markup, parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )

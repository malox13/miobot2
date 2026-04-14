from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import (
    get_activity, get_activities, get_items, get_completion, set_completion,
    get_period_key, get_activity_completion_rate, get_history, get_streak,
    delete_activity, delete_item, update_activity_timeframe, save_snapshot,
    get_all_user_ids
)
from handlers.start import show_main_menu

MAIN_MENU = 0
CREATE_ACTIVITY_NAME = 1
CREATE_ITEM_TYPE = 2
ADD_CHECKBOX_LABEL = 3
ADD_COUNTER_TARGET = 4
ADD_MORE_ITEMS = 5
EDIT_ACTIVITY = 6
CONFIRM_DELETE = 7

TIMEFRAME_EMOJI = {"daily": "📅", "weekly": "📆", "monthly": "🗓️"}
TIMEFRAME_LABEL = {"daily": "Giornaliero", "weekly": "Settimanale", "monthly": "Mensile"}

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    # ── Main menu ──────────────────────────────────────────────────────────
    if data == "main_menu":
        await show_main_menu(update, context, user_id)
        return MAIN_MENU

    # ── New activity ───────────────────────────────────────────────────────
    if data == "new_activity":
        context.user_data["creating"] = {"items": []}
        await query.edit_message_text(
            "✏️ *Nuova attività*\n\nCome vuoi chiamarla?\n\n_(Scrivi il nome e invia)_",
            parse_mode="Markdown"
        )
        return CREATE_ACTIVITY_NAME

    # ── Activity dashboard ─────────────────────────────────────────────────
    if data.startswith("activity:"):
        act_id = int(data.split(":")[1])
        await show_activity_dashboard(update, context, user_id, act_id)
        return MAIN_MENU

    # ── Toggle checkbox ────────────────────────────────────────────────────
    if data.startswith("toggle:"):
        _, item_id_str, act_id_str = data.split(":")
        item_id = int(item_id_str)
        act_id = int(act_id_str)
        act = get_activity(act_id)
        period_key = get_period_key(act["timeframe"])
        comp = get_completion(item_id, user_id, period_key)
        current = comp["value"] if comp else 0
        new_val = 0 if current == 1 else 1
        set_completion(item_id, user_id, period_key, new_val)
        save_snapshot(user_id, act_id, period_key)
        await show_activity_dashboard(update, context, user_id, act_id)
        return MAIN_MENU

    # ── Counter increment ──────────────────────────────────────────────────
    if data.startswith("inc:"):
        _, item_id_str, act_id_str = data.split(":")
        item_id = int(item_id_str)
        act_id = int(act_id_str)
        act = get_activity(act_id)
        period_key = get_period_key(act["timeframe"])
        items = get_items(act_id)
        item = next((i for i in items if i["id"] == item_id), None)
        if item:
            comp = get_completion(item_id, user_id, period_key)
            current = comp["value"] if comp else 0
            target = item["counter_target"] or 1
            new_val = min(current + 1, target)
            set_completion(item_id, user_id, period_key, new_val)
            save_snapshot(user_id, act_id, period_key)
        await show_activity_dashboard(update, context, user_id, act_id)
        return MAIN_MENU

    # ── Counter decrement ──────────────────────────────────────────────────
    if data.startswith("dec:"):
        _, item_id_str, act_id_str = data.split(":")
        item_id = int(item_id_str)
        act_id = int(act_id_str)
        act = get_activity(act_id)
        period_key = get_period_key(act["timeframe"])
        comp = get_completion(item_id, user_id, period_key)
        current = comp["value"] if comp else 0
        new_val = max(current - 1, 0)
        set_completion(item_id, user_id, period_key, new_val)
        save_snapshot(user_id, act_id, period_key)
        await show_activity_dashboard(update, context, user_id, act_id)
        return MAIN_MENU

    # ── Activity stats ─────────────────────────────────────────────────────
    if data.startswith("stats:"):
        act_id = int(data.split(":")[1])
        await show_activity_stats(update, context, user_id, act_id)
        return MAIN_MENU

    # ── Global stats ───────────────────────────────────────────────────────
    if data == "global_stats":
        await show_global_stats(update, context, user_id)
        return MAIN_MENU

    # ── Edit activity menu ─────────────────────────────────────────────────
    if data.startswith("edit:"):
        act_id = int(data.split(":")[1])
        act = get_activity(act_id)
        keyboard = [
            [InlineKeyboardButton("⏱️ Cambia frequenza", callback_data=f"change_tf:{act_id}")],
            [InlineKeyboardButton("➕ Aggiungi voce", callback_data=f"add_item:{act_id}")],
            [InlineKeyboardButton("🗑️ Elimina attività", callback_data=f"ask_delete:{act_id}")],
            [InlineKeyboardButton("◀️ Torna", callback_data=f"activity:{act_id}")],
        ]
        await query.edit_message_text(
            f"⚙️ *Modifica: {act['name']}*\n\nCosa vuoi cambiare?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return EDIT_ACTIVITY

    # ── Change timeframe ───────────────────────────────────────────────────
    if data.startswith("change_tf:"):
        act_id = int(data.split(":")[1])
        keyboard = [
            [InlineKeyboardButton("📅 Giornaliero", callback_data=f"set_tf:{act_id}:daily")],
            [InlineKeyboardButton("📆 Settimanale", callback_data=f"set_tf:{act_id}:weekly")],
            [InlineKeyboardButton("🗓️ Mensile", callback_data=f"set_tf:{act_id}:monthly")],
            [InlineKeyboardButton("◀️ Indietro", callback_data=f"edit:{act_id}")],
        ]
        await query.edit_message_text(
            "⏱️ Scegli la frequenza di reset:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return EDIT_ACTIVITY

    if data.startswith("set_tf:"):
        _, act_id_str, tf = data.split(":")
        act_id = int(act_id_str)
        update_activity_timeframe(act_id, tf)
        await show_activity_dashboard(update, context, user_id, act_id)
        return MAIN_MENU

    # ── Add item to existing activity ──────────────────────────────────────
    if data.startswith("add_item:"):
        act_id = int(data.split(":")[1])
        context.user_data["adding_to"] = act_id
        keyboard = [
            [InlineKeyboardButton("☑️ Checkbox (sì/no)", callback_data="item_type:checkbox")],
            [InlineKeyboardButton("🔢 Counter (numero)", callback_data="item_type:counter")],
            [InlineKeyboardButton("◀️ Annulla", callback_data=f"edit:{act_id}")],
        ]
        await query.edit_message_text(
            "Che tipo di voce vuoi aggiungere?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return CREATE_ITEM_TYPE

    # ── Item type selection (during creation) ──────────────────────────────
    if data.startswith("item_type:"):
        item_type = data.split(":")[1]
        context.user_data.setdefault("creating", {})["pending_type"] = item_type
        if item_type == "checkbox":
            await query.edit_message_text(
                "☑️ Scrivi il nome di questa checkbox:\n_(es. 'Lettura mattina 20 pagine')_",
                parse_mode="Markdown"
            )
            return ADD_CHECKBOX_LABEL
        else:
            await query.edit_message_text(
                "🔢 Scrivi il nome del counter:\n_(es. 'Quiz patente')_",
                parse_mode="Markdown"
            )
            return ADD_COUNTER_TARGET

    # ── Ask delete confirmation ────────────────────────────────────────────
    if data.startswith("ask_delete:"):
        act_id = int(data.split(":")[1])
        act = get_activity(act_id)
        keyboard = [
            [InlineKeyboardButton("✅ Sì, elimina", callback_data=f"confirm_delete:{act_id}")],
            [InlineKeyboardButton("❌ No, annulla", callback_data=f"edit:{act_id}")],
        ]
        await query.edit_message_text(
            f"⚠️ Sei sicuro di voler eliminare *{act['name']}*?\n\nTutti i dati saranno persi.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return CONFIRM_DELETE

    if data.startswith("confirm_delete:"):
        act_id = int(data.split(":")[1])
        delete_activity(act_id)
        await show_main_menu(update, context, user_id)
        return MAIN_MENU

    # ── Delete single item ─────────────────────────────────────────────────
    if data.startswith("del_item:"):
        _, item_id_str, act_id_str = data.split(":")
        delete_item(int(item_id_str))
        await show_activity_dashboard(update, context, user_id, int(act_id_str))
        return MAIN_MENU

    # ── Timeframe selection (during creation) ──────────────────────────────
    if data.startswith("tf:"):
        tf = data.split(":")[1]
        creating = context.user_data.get("creating", {})
        creating["timeframe"] = tf
        context.user_data["creating"] = creating
        await _finalize_activity(update, context, user_id)
        return MAIN_MENU

    # ── Add more items (during creation) ──────────────────────────────────
    if data == "add_more":
        keyboard = [
            [InlineKeyboardButton("☑️ Checkbox", callback_data="item_type:checkbox")],
            [InlineKeyboardButton("🔢 Counter", callback_data="item_type:counter")],
        ]
        await query.edit_message_text(
            "Che tipo di voce vuoi aggiungere?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return CREATE_ITEM_TYPE

    if data == "done_adding":
        keyboard = [
            [InlineKeyboardButton("📅 Giornaliero", callback_data="tf:daily")],
            [InlineKeyboardButton("📆 Settimanale", callback_data="tf:weekly")],
            [InlineKeyboardButton("🗓️ Mensile", callback_data="tf:monthly")],
        ]
        creating = context.user_data.get("creating", {})
        items_preview = "\n".join(f"  • {i['label']}" for i in creating.get("items", []))
        await query.edit_message_text(
            f"⏱️ Con quale frequenza si resetta *{creating.get('name', '')}*?\n\n{items_preview}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ADD_MORE_ITEMS

    return MAIN_MENU


async def show_activity_dashboard(update, context, user_id: int, act_id: int):
    act = get_activity(act_id)
    if not act:
        await show_main_menu(update, context, user_id)
        return

    items = get_items(act_id)
    period_key = get_period_key(act["timeframe"])
    tf_label = {"daily": "Oggi", "weekly": "Questa settimana", "monthly": "Questo mese"}.get(act["timeframe"], "Oggi")
    tf_emoji = TIMEFRAME_EMOJI.get(act["timeframe"], "📅")

    comp, total = get_activity_completion_rate(act_id, user_id, period_key)
    pct = int(comp / total * 100) if total > 0 else 0
    bar = _progress_bar(pct)

    text = f"*{act['name']}* {tf_emoji}\n_{tf_label}_ — {comp}/{total} completati\n{bar} {pct}%\n\n"

    keyboard = []
    for item in items:
        c = get_completion(item["id"], user_id, period_key)
        val = c["value"] if c else 0

        if item["type"] == "checkbox":
            icon = "✅" if val == 1 else "⬜"
            row = [
                InlineKeyboardButton(f"{icon} {item['label']}", callback_data=f"toggle:{item['id']}:{act_id}"),
                InlineKeyboardButton("🗑️", callback_data=f"del_item:{item['id']}:{act_id}"),
            ]
        else:
            target = item["counter_target"] or 1
            done = val >= target
            icon = "✅" if done else "🔢"
            counter_bar = f"{val}/{target}"
            row = [
                InlineKeyboardButton(f"➖", callback_data=f"dec:{item['id']}:{act_id}"),
                InlineKeyboardButton(f"{icon} {item['label']} {counter_bar}", callback_data=f"inc:{item['id']}:{act_id}"),
                InlineKeyboardButton(f"➕", callback_data=f"inc:{item['id']}:{act_id}"),
            ]
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("📊 Stats", callback_data=f"stats:{act_id}"),
        InlineKeyboardButton("⚙️ Modifica", callback_data=f"edit:{act_id}"),
    ])
    keyboard.append([InlineKeyboardButton("◀️ Menu principale", callback_data="main_menu")])

    query = update.callback_query
    try:
        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
    except Exception:
        await query.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )


async def show_activity_stats(update, context, user_id: int, act_id: int):
    act = get_activity(act_id)
    history = get_history(user_id, act_id, limit=60)
    streak = get_streak(user_id, act_id)

    total_days = len(history)
    perfect_days = sum(1 for r in history if r["total_items"] > 0 and r["completed_items"] >= r["total_items"])
    consistency = int(perfect_days / total_days * 100) if total_days > 0 else 0

    # Build block grid (most recent last, 10 per row)
    blocks = []
    for r in reversed(history):
        if r["total_items"] == 0:
            blocks.append("⬜")
        elif r["completed_items"] >= r["total_items"]:
            blocks.append("🟩")
        elif r["completed_items"] > 0:
            blocks.append("🟨")
        else:
            blocks.append("🟥")

    # Pad to multiple of 7
    while len(blocks) % 7 != 0:
        blocks.insert(0, "⬛")

    grid_lines = []
    for i in range(0, len(blocks), 7):
        grid_lines.append("".join(blocks[i:i+7]))

    grid = "\n".join(grid_lines[-8:]) if grid_lines else "_(nessun dato)_"

    text = (
        f"📊 *Stats: {act['name']}*\n\n"
        f"🔥 Streak attuale: *{streak} giorni*\n"
        f"🎯 Consistenza: *{consistency}%* ({perfect_days}/{total_days} periodi)\n\n"
        f"*Storico recente* (🟩=completo 🟨=parziale 🟥=zero)\n{grid}\n"
    )

    keyboard = [[InlineKeyboardButton("◀️ Torna", callback_data=f"activity:{act_id}")]]
    query = update.callback_query
    try:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except Exception:
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def show_global_stats(update, context, user_id: int):
    activities = get_activities(user_id)
    if not activities:
        await update.callback_query.edit_message_text("Nessuna attività ancora!")
        return

    lines = ["📊 *Statistiche globali*\n"]
    for act in activities:
        streak = get_streak(user_id, act["id"])
        history = get_history(user_id, act["id"], limit=30)
        perfect = sum(1 for r in history if r["total_items"] > 0 and r["completed_items"] >= r["total_items"])
        consistency = int(perfect / len(history) * 100) if history else 0
        tf_emoji = TIMEFRAME_EMOJI.get(act["timeframe"], "📅")
        lines.append(f"{tf_emoji} *{act['name']}*\n  🔥 {streak}gg streak  |  🎯 {consistency}% consistenza")

    text = "\n\n".join(lines)
    keyboard = [[InlineKeyboardButton("◀️ Menu principale", callback_data="main_menu")]]
    try:
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
    except Exception:
        pass


async def _finalize_activity(update, context, user_id: int):
    from database import create_activity, add_item
    creating = context.user_data.get("creating", {})
    name = creating.get("name", "Nuova attività")
    tf = creating.get("timeframe", "daily")
    items = creating.get("items", [])

    act_id = create_activity(user_id, name, tf)
    for item in items:
        add_item(act_id, item["type"], item["label"], item.get("target"))

    context.user_data.pop("creating", None)
    context.user_data.pop("adding_to", None)

    await show_activity_dashboard(update, context, user_id, act_id)


def _progress_bar(pct: int, length: int = 10) -> str:
    filled = int(pct / 100 * length)
    return "█" * filled + "░" * (length - filled)

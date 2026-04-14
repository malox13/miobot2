from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

ADD_CHECKBOX_LABEL = 3
ADD_COUNTER_TARGET = 4
ADD_MORE_ITEMS = 5
CREATE_ITEM_TYPE = 2


async def handle_activity_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("Il nome non può essere vuoto. Riprova:")
        return 1  # CREATE_ACTIVITY_NAME

    context.user_data.setdefault("creating", {"items": []})["name"] = name

    keyboard = [
        [InlineKeyboardButton("☑️ Checkbox (sì/no)", callback_data="item_type:checkbox")],
        [InlineKeyboardButton("🔢 Counter (numero)", callback_data="item_type:counter")],
    ]
    await update.message.reply_text(
        f"✅ Attività: *{name}*\n\nAggiungi la prima voce — che tipo?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return CREATE_ITEM_TYPE


async def handle_checkbox_label(update: Update, context: ContextTypes.DEFAULT_TYPE):
    label = update.message.text.strip()
    if not label:
        await update.message.reply_text("Il nome non può essere vuoto. Riprova:")
        return ADD_CHECKBOX_LABEL

    creating = context.user_data.get("creating", {})
    adding_to = context.user_data.get("adding_to")

    if adding_to:
        # Adding to existing activity
        from database import add_item
        add_item(adding_to, "checkbox", label)
        context.user_data.pop("adding_to", None)
        from handlers.button_handler import show_activity_dashboard
        # Simulate callback query context - use a workaround
        await update.message.reply_text(f"☑️ Checkbox *{label}* aggiunta!", parse_mode="Markdown")
        # Show dashboard
        keyboard = [[InlineKeyboardButton("◀️ Torna all'attività", callback_data=f"activity:{adding_to}")]]
        await update.message.reply_text("Torna all'attività:", reply_markup=InlineKeyboardMarkup(keyboard))
        return 0  # MAIN_MENU
    else:
        items = creating.setdefault("items", [])
        items.append({"type": "checkbox", "label": label})

        keyboard = [
            [InlineKeyboardButton("➕ Aggiungi altra voce", callback_data="add_more")],
            [InlineKeyboardButton("✅ Fatto, scegli frequenza", callback_data="done_adding")],
        ]
        await update.message.reply_text(
            f"☑️ Aggiunto: *{label}*\n\nVuoi aggiungere un'altra voce?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return 5  # ADD_MORE_ITEMS


async def handle_counter_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called after user sends counter name, then ask for target"""
    text = update.message.text.strip()
    creating = context.user_data.get("creating", {})
    adding_to = context.user_data.get("adding_to")

    # If we're waiting for the label first
    if not creating.get("pending_counter_label") and (not adding_to or not context.user_data.get("pending_counter_label")):
        # This is the label
        context.user_data["pending_counter_label"] = text
        await update.message.reply_text(
            f"🔢 Counter: *{text}*\n\nQuante volte deve arrivare per essere completato?\n_(Scrivi un numero, es. 10)_",
            parse_mode="Markdown"
        )
        return ADD_COUNTER_TARGET
    else:
        # This is the target number
        label = context.user_data.pop("pending_counter_label", "Counter")
        try:
            target = int(text)
            if target < 1:
                raise ValueError()
        except ValueError:
            await update.message.reply_text("Inserisci un numero valido (es. 10):")
            context.user_data["pending_counter_label"] = label
            return ADD_COUNTER_TARGET

        if adding_to:
            from database import add_item
            add_item(adding_to, "counter", label, target)
            context.user_data.pop("adding_to", None)
            await update.message.reply_text(f"🔢 Counter *{label}* (obiettivo: {target}) aggiunto!", parse_mode="Markdown")
            keyboard = [[InlineKeyboardButton("◀️ Torna all'attività", callback_data=f"activity:{adding_to}")]]
            await update.message.reply_text("Torna all'attività:", reply_markup=InlineKeyboardMarkup(keyboard))
            return 0  # MAIN_MENU
        else:
            items = creating.setdefault("items", [])
            items.append({"type": "counter", "label": label, "target": target})
            keyboard = [
                [InlineKeyboardButton("➕ Aggiungi altra voce", callback_data="add_more")],
                [InlineKeyboardButton("✅ Fatto, scegli frequenza", callback_data="done_adding")],
            ]
            await update.message.reply_text(
                f"🔢 Aggiunto: *{label}* (obiettivo: {target})\n\nVuoi aggiungere un'altra voce?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return 5  # ADD_MORE_ITEMS

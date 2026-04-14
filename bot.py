import logging
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from handlers import start, button_handler, message_handler
from scheduler import setup_scheduler
from database import init_db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(
    MAIN_MENU, CREATE_ACTIVITY_NAME, CREATE_ITEM_TYPE,
    ADD_CHECKBOX_LABEL, ADD_COUNTER_TARGET, ADD_MORE_ITEMS,
    EDIT_ACTIVITY, CONFIRM_DELETE
) = range(8)

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN non trovato nelle variabili d'ambiente!")

    init_db()

    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start.start_command)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(button_handler.handle_button),
                CommandHandler("start", start.start_command),
            ],
            CREATE_ACTIVITY_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler.handle_activity_name),
                CallbackQueryHandler(button_handler.handle_button),
            ],
            CREATE_ITEM_TYPE: [
                CallbackQueryHandler(button_handler.handle_button),
            ],
            ADD_CHECKBOX_LABEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler.handle_checkbox_label),
                CallbackQueryHandler(button_handler.handle_button),
            ],
            ADD_COUNTER_TARGET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler.handle_counter_target),
                CallbackQueryHandler(button_handler.handle_button),
            ],
            ADD_MORE_ITEMS: [
                CallbackQueryHandler(button_handler.handle_button),
            ],
            EDIT_ACTIVITY: [
                CallbackQueryHandler(button_handler.handle_button),
            ],
            CONFIRM_DELETE: [
                CallbackQueryHandler(button_handler.handle_button),
            ],
        },
        fallbacks=[
            CommandHandler("start", start.start_command),
            CommandHandler("menu", start.start_command),
        ],
        per_message=False,
        allow_reentry=True,
    )

    application.add_handler(conv_handler)
    setup_scheduler(application)

    logger.info("Bot avviato!")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()

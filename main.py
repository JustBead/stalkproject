import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
)
from database import Database
from payments import Payments
from fake_profiles import FakeProfiles
from admin import AdminPanel
from config import BOT_TOKEN, ADMIN_USERNAME, ADMIN_PASSWORD

# Logger setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Instantiate helpers
db = Database()
payments = Payments()
fake_profiles = FakeProfiles()
admin_panel = AdminPanel(ADMIN_USERNAME, ADMIN_PASSWORD, db)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    user = update.effective_user
    db.add_user(user.id, user.username)

    keyboard = [
        [InlineKeyboardButton("🔍 Stalklayanları Gör", callback_data="see_stalkers")],
        [InlineKeyboardButton("💵 Fiyat Menüsü", callback_data="pricing")],
        [InlineKeyboardButton("🎁 Referans Sistemi", callback_data="referral")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Merhaba {user.first_name}! Sahte stalk gösterme botuna hoş geldiniz.",
        reply_markup=reply_markup
    )


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button clicks."""
    query = update.callback_query
    await query.answer()

    if query.data == "see_stalkers":
        if db.user_has_free_quota(query.from_user.id):
            stalkers = fake_profiles.get_random_profiles(query.from_user.id, blur=True)
            stalkers_text = "\n".join([f"@{s}" for s in stalkers])
            await query.edit_message_text(
                f"Bugün seni stalklayanlar (bulanık):\n{stalkers_text}\n\n"
                "Premium üyelik satın alarak tüm profilleri görebilirsiniz."
            )
            db.decrement_free_quota(query.from_user.id)
        else:
            await query.edit_message_text(
                "Ücretsiz hakkınız bitti. Lütfen üyelik satın alarak devam edin."
            )

    elif query.data == "pricing":
        exchange_rate = 30  # 1 USD = 30 TL olarak belirlenmiştir.
        pricing_text = (
            "💵 Fiyat Menüsü:\n"
            f"• Günlük: 30 TL (~{round(30 / exchange_rate)} USD)\n"
            f"• Haftalık: 200 TL (~{round(200 / exchange_rate)} USD)\n"
            f"• Aylık: 500 TL (~{round(500 / exchange_rate)} USD)\n"
            f"• Yıllık: 1500 TL (~{round(1500 / exchange_rate)} USD)\n\n"
            "Ödeme yöntemleri: USDT TRC20, Papara, IBAN\n\n"
            "Ödeme yaptıktan sonra dekontu gönderin."
        )
        await query.edit_message_text(pricing_text)

    elif query.data == "referral":
        referral_code = db.get_referral_code(query.from_user.id)
        referral_text = (
            f"🎁 Referans Sistemi:\n"
            f"Arkadaşlarını davet et ve 15 referans yaparak 1 hafta ücretsiz premium kazan!\n"
            f"Senin referans kodun: `{referral_code}`\n"
            f"Referans linki: https://t.me/{context.bot.username}?start={referral_code}"
        )
        await query.edit_message_text(referral_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user messages."""
    user = update.effective_user
    text = update.message.text

    if context.user_data.get('awaiting_username'):
        username = text.strip()
        stalkers = fake_profiles.get_random_profiles(user.id, blur=False)
        db.save_query(user.id, username, stalkers)
        stalkers_text = "\n".join([f"@{s}" for s in stalkers])
        await update.message.reply_text(
            f"Bugün seni stalklayanlar:\n{stalkers_text}"
        )
        context.user_data['awaiting_username'] = False

    elif text.startswith("/odeme"):
        await payments.request_payment(update, context)

    elif text.startswith("/odemeyontemleri"):
        await payments.show_payment_methods(update, context)

    elif text.startswith("/justadmin"):
        await admin_panel.handle_admin_entry(update, context)

    elif text.startswith("admin:"):
        await admin_panel.authenticate_admin(update, context)


def main():
    """Start the bot."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("odeme", payments.request_payment))
    application.add_handler(CommandHandler("odemeyontemleri", payments.show_payment_methods))
    application.add_handler(CommandHandler("justadmin", admin_panel.handle_admin_entry))

    # Button callback handler
    application.add_handler(CallbackQueryHandler(handle_button))

    # Message handler for usernames
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling
    application.run_polling()


if __name__ == "__main__":
    main()

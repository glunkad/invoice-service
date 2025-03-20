import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import random
import string
from datetime import datetime
from utils import generate_pdf

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

PROPERTY_NAME = "River's Edge Villa"
LOCATION = "https://maps.app.goo.gl/VhdYPepvED3ivRfq5"
HOST_NAME = "Gunjan"
CANCELLATION_POLICY = "No cancellation"

# Define conversation states
(GUEST_NAME, CHECK_IN, CHECK_OUT, TOTAL_AMOUNT, AMOUNT_PAID, GUEST_COUNT, CONFIRMATION_CODE) = range(7)


def generate_booking_id() -> str:
    """Generate a 10-character alphanumeric booking ID (Airbnb-style)."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the booking process."""
    context.user_data.clear()
    context.user_data["booking_id"] = generate_booking_id()

    # Auto-fill fixed property details
    context.user_data.update({
        "property_name": PROPERTY_NAME,
        "location": LOCATION,
        "host_name": HOST_NAME,
        "cancellation_policy": CANCELLATION_POLICY
    })

    await update.message.reply_text(
        "Welcome to *River's Edge Villa*! 🏡\n\nEnter your *Guest Name*:",
        parse_mode='Markdown'
    )
    return GUEST_NAME


async def get_guest_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["guest_name"] = update.message.text.strip()
    await update.message.reply_text("Enter *Check-in Date (YYYY-MM-DD HH:MM)*:", parse_mode='Markdown')
    return CHECK_IN


async def get_check_in(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        check_in = datetime.strptime(update.message.text, "%Y-%m-%d %H:%M")
        if check_in < datetime.now():
            await update.message.reply_text("❌ Check-in date cannot be in the past!")
            return CHECK_IN
        context.user_data["check_in"] = check_in.isoformat()
        await update.message.reply_text("Enter *Check-out Date (YYYY-MM-DD HH:MM)*:", parse_mode='Markdown')
        return CHECK_OUT
    except ValueError:
        await update.message.reply_text("❌ Invalid date! Use format: YYYY-MM-DD HH:MM")
        return CHECK_IN


async def get_check_out(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        check_out = datetime.strptime(update.message.text, "%Y-%m-%d %H:%M")
        check_in = datetime.fromisoformat(context.user_data["check_in"])
        if check_out <= check_in:
            await update.message.reply_text("❌ Check-out must be after check-in!")
            return CHECK_OUT
        context.user_data["check_out"] = check_out.isoformat()
        await update.message.reply_text("Enter *Total Amount*:", parse_mode='Markdown')
        return TOTAL_AMOUNT
    except ValueError:
        await update.message.reply_text("❌ Invalid date! Use format: YYYY-MM-DD HH:MM")
        return CHECK_OUT


async def get_total_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        amount = float(update.message.text)
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be positive!")
            return TOTAL_AMOUNT
        context.user_data["total_amount"] = amount
        await update.message.reply_text("Enter *Amount Paid*:", parse_mode='Markdown')
        return AMOUNT_PAID
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")
        return TOTAL_AMOUNT


async def get_amount_paid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        amount = float(update.message.text)
        if amount < 0 or amount > context.user_data["total_amount"]:
            await update.message.reply_text("❌ Amount paid must be between 0 and total amount!")
            return AMOUNT_PAID
        context.user_data["amount_paid"] = amount
        await update.message.reply_text("Enter *Number of Guests*:", parse_mode='Markdown')
        return GUEST_COUNT
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")
        return AMOUNT_PAID


async def get_guest_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        count = int(update.message.text)
        if count <= 0:
            await update.message.reply_text("❌ Guest count must be positive!")
            return GUEST_COUNT
        context.user_data["guest_count"] = count
        await update.message.reply_text("Enter *Confirmation Code*:", parse_mode='Markdown')
        return CONFIRMATION_CODE
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")
        return GUEST_COUNT


async def get_confirmation_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["confirmation_code"] = update.message.text.strip()

    # Generate PDF Invoice
    try:
        pdf_path = generate_pdf(context.user_data)

        # Send PDF
        with open(pdf_path, "rb") as pdf_file:
            await update.message.reply_document(
                document=pdf_file,
                filename=f"invoice_{context.user_data['booking_id']}.pdf",
                caption="✅ Booking confirmed! Your invoice is attached."
            )

        # Clean up temporary file
        import os
        os.remove(pdf_path)
    except Exception as e:
        await update.message.reply_text(f"❌ Error generating invoice: {str(e)}")
        return ConversationHandler.END

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the booking process."""
    await update.message.reply_text("❌ Booking process canceled.")
    return ConversationHandler.END


def main() -> None:
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GUEST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_guest_name)],
            CHECK_IN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_check_in)],
            CHECK_OUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_check_out)],
            TOTAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_total_amount)],
            AMOUNT_PAID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount_paid)],
            GUEST_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_guest_count)],
            CONFIRMATION_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_confirmation_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()
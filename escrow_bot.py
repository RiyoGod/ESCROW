import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder
from config import TOKEN, LOGS_CHAT_ID, ADMINS

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

deals = {}

# Start Command
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.reply(
        "Welcome to AutoEscrow Bot! Use /create to start a deal."
    )

# Create Command
@dp.message(Command("create"))
async def create_command(message: types.Message):
    await message.reply(
        "Fill this form to start the deal:\n\n"
        "Seller :\n"
        "Buyer :\n"
        "Deal Info :\n"
        "Amount (In USDT) :\n"
        "Time To Complete : (in minutes)\n\n"
        "Reply to this message with the filled form."
    )

# Form Reply Handler
@dp.message()
async def handle_form_reply(message: types.Message):
    if message.reply_to_message and "Fill this form to start the deal:" in message.reply_to_message.text:
        lines = message.text.strip().split("\n")

        if len(lines) < 5:
            await message.reply("Invalid format. Please fill all fields correctly.")
            return

        seller = lines[0].replace("Seller :", "").strip()
        buyer = lines[1].replace("Buyer :", "").strip()
        deal_info = lines[2].replace("Deal Info :", "").strip()
        amount = lines[3].replace("Amount (In USDT) :", "").strip()
        time_to_complete = lines[4].replace("Time To Complete :", "").strip()

        try:
            fee = calculate_fee(amount)
        except Exception as e:
            await message.reply(f"Failed to calculate fee: {e}")
            return

        deal_id = message.message_id
        deals[deal_id] = {
            "creator": message.from_user.username,
            "seller": seller,
            "buyer": buyer,
            "info": deal_info,
            "amount": amount,
            "time": time_to_complete,
            "fee": fee,
            "confirmed_seller": False,
            "confirmed_buyer": False,
        }

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"I am Seller ({seller})", callback_data=f"confirm_seller_{deal_id}")],
                [InlineKeyboardButton(text=f"I am Buyer ({buyer})", callback_data=f"confirm_buyer_{deal_id}")]
            ]
        )

        deal_text = (
            f"**New Deal Created!**\n\n"
            f"**Deal ID:** {deal_id}\n"
            f"**Created By:** @{message.from_user.username}\n"
            f"**Seller:** {seller}\n"
            f"**Buyer:** {buyer}\n"
            f"**Deal Info:** {deal_info}\n"
            f"**Amount:** {amount} USDT\n"
            f"**Escrow Fee (2%):** {fee} USDT\n"
            f"**Time To Complete:** {time_to_complete} Minutes"
        )

        await bot.send_message(LOGS_CHAT_ID, deal_text, reply_markup=keyboard, parse_mode="Markdown")
        await message.reply("Deal has been sent to the logs group for confirmation!")

# Fee Calculation
def calculate_fee(amount):
    try:
        amount = float(amount)
        fee = amount * 0.02
        return round(fee, 2)
    except ValueError:
        raise ValueError("Invalid amount provided")

# Seller Confirmation
@dp.callback_query(lambda c: c.data.startswith("confirm_seller_"))
async def confirm_seller(callback: types.CallbackQuery):
    deal_id = int(callback.data.split("_")[-1])

    if deal_id not in deals:
        await callback.answer("Deal not found or expired.")
        return

    deals[deal_id]["confirmed_seller"] = True
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ Seller Confirmed!", 
        reply_markup=get_updated_keyboard(deal_id)
    )
    await callback.answer("You confirmed as Seller.")

# Buyer Confirmation
@dp.callback_query(lambda c: c.data.startswith("confirm_buyer_"))
async def confirm_buyer(callback: types.CallbackQuery):
    deal_id = int(callback.data.split("_")[-1])

    if deal_id not in deals:
        await callback.answer("Deal not found or expired.")
        return

    deals[deal_id]["confirmed_buyer"] = True
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ Buyer Confirmed!", 
        reply_markup=get_updated_keyboard(deal_id)
    )
    await callback.answer("You confirmed as Buyer.")

# Keyboard Updater
def get_updated_keyboard(deal_id):
    deal = deals.get(deal_id)
    buttons = []

    if not deal["confirmed_seller"]:
        buttons.append(InlineKeyboardButton(
            text=f"I am Seller ({deal['seller']})", callback_data=f"confirm_seller_{deal_id}")
        )
    if not deal["confirmed_buyer"]:
        buttons.append(InlineKeyboardButton(
            text=f"I am Buyer ({deal['buyer']})", callback_data=f"confirm_buyer_{deal_id}")
        )

    if not buttons:
        return None  # All confirmed
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

# Start Bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

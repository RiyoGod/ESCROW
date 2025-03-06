import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN, LOGS_CHAT_ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

deal_data = {}

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.reply("Welcome to AutoEscrow Bot! Use /create to start a deal.")

@dp.message(Command("create"))
async def create_command(message: types.Message):
    if message.chat.type != "group" and message.chat.type != "supergroup":
        await message.reply("You need to create a group with the seller and buyer, then add this bot and use /create.")
        return

    deal_data[message.chat.id] = {
        "seller": None,
        "buyer": None,
        "info": None,
        "amount": None,
        "time": None,
        "fees": None
    }

    await message.reply(
        "Fill this form to start the deal:\n\n"
        "Seller: @username\n"
        "Buyer: @username\n"
        "Deal Info: Short description\n"
        "Amount (In USDT):\n"
        "Time To Complete: (in minutes)\n\n"
        "Reply to this message with the filled form."
    )

@dp.message(F.reply_to_message)
async def handle_form_reply(message: types.Message):
    if not message.reply_to_message.text.startswith("Fill this form to start the deal"):
        return

    lines = message.text.strip().split("\n")
    if len(lines) < 5:
        await message.reply("Invalid format. Please fill all fields.")
        return

    deal_data[message.chat.id].update({
        "seller": lines[0].replace("Seller:", "").strip(),
        "buyer": lines[1].replace("Buyer:", "").strip(),
        "info": lines[2].replace("Deal Info:", "").strip(),
        "amount": lines[3].replace("Amount (In USDT):", "").strip(),
        "time": lines[4].replace("Time To Complete:", "").strip(),
    })

    confirm_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="I am Seller", callback_data="confirm_seller")],
            [InlineKeyboardButton(text="I am Buyer", callback_data="confirm_buyer")]
        ]
    )

    await message.reply(
        "Form received! Now seller and buyer must confirm their roles:",
        reply_markup=confirm_buttons
    )

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_roles(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    user = callback.from_user.username

    if callback.data == "confirm_seller":
        if deal_data[chat_id].get("seller_confirmed"):
            await callback.answer("Seller already confirmed.")
            return
        if f"@{user}" != deal_data[chat_id]["seller"]:
            await callback.answer("You are not the seller!")
            return
        deal_data[chat_id]["seller_confirmed"] = user
        await callback.message.reply(f"✅ Seller confirmed by @{user}")
    elif callback.data == "confirm_buyer":
        if deal_data[chat_id].get("buyer_confirmed"):
            await callback.answer("Buyer already confirmed.")
            return
        if f"@{user}" != deal_data[chat_id]["buyer"]:
            await callback.answer("You are not the buyer!")
            return
        deal_data[chat_id]["buyer_confirmed"] = user
        await callback.message.reply(f"✅ Buyer confirmed by @{user}")

    if "seller_confirmed" in deal_data[chat_id] and "buyer_confirmed" in deal_data[chat_id]:
        await ask_fee_preference(chat_id)

async def ask_fee_preference(chat_id):
    fee_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="I will pay full fees", callback_data="fees_full")],
            [InlineKeyboardButton(text="Split fees 50/50", callback_data="fees_split")]
        ]
    )
    await bot.send_message(chat_id, "How will the escrow fee be paid?", reply_markup=fee_buttons)

@dp.callback_query(F.data.startswith("fees_"))
async def confirm_fees(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    amount = float(deal_data[chat_id]["amount"])
    fee = round(amount * 0.02, 2)

    if callback.data == "fees_full":
        payer = callback.from_user.username
        deal_data[chat_id]["fees"] = f"Full fees ({fee} USDT) paid by @{payer}"
    elif callback.data == "fees_split":
        deal_data[chat_id]["fees"] = f"Split fees (each pays {fee / 2} USDT)"

    await callback.message.reply("✅ Fee agreement set.")
    await send_deal_to_logs(chat_id)

async def send_deal_to_logs(chat_id):
    deal = deal_data[chat_id]
    log_text = (
        f"**New Deal Created!**\n\n"
        f"Group: <b>{(await bot.get_chat(chat_id)).title}</b>\n"
        f"Seller: {deal['seller']}\n"
        f"Buyer: {deal['buyer']}\n"
        f"Deal Info: {deal['info']}\n"
        f"Amount: {deal['amount']} USDT\n"
        f"Time To Complete: {deal['time']} minutes\n"
        f"Escrow Fee: {deal['fees']}\n\n"
        f"Deal created and confirmed in group."
    )

    await bot.send_message(LOGS_CHAT_ID, log_text)
    await bot.send_message(chat_id, "Deal created and sent to logs for admin review.")

# Start Bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

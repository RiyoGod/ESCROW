import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
import config

bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Temporary in-memory deal storage
deals = {}

def deal_buttons(deal_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Seller Confirm", callback_data=f"confirm:seller:{deal_id}")],
            [InlineKeyboardButton(text="✅ Buyer Confirm", callback_data=f"confirm:buyer:{deal_id}")]
        ]
    )

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.reply("Welcome to Escrow Bot! Use /create to start a deal (admin only).")

@dp.message(Command("create"))
async def create_deal(message: Message):
    if message.from_user.id != config.ADMIN_ID:
        return await message.reply("Only the admin can create deals.")
    
    await message.reply(
        "Fill this form in this format:\n\n"
        "Seller: @username\n"
        "Buyer: @username\n"
        "Deal Info: Brief description\n"
        "Amount: 50 USDT\n"
        "Time: 24 hours"
    )

@dp.message(F.text.regexp(r"Seller:\s?@(\w+)\nBuyer:\s?@(\w+)\nDeal Info:\s?(.+)\nAmount:\s?(\d+)\s?USDT\nTime:\s?(\d+)\s?hours"))
async def process_deal_form(message: Message):
    if message.chat.id != config.GROUP_ID:
        return  # Only allow deal forms inside the configured group

    lines = message.text.strip().split("\n")
    seller = lines[0].split("@")[1].strip()
    buyer = lines[1].split("@")[1].strip()
    deal_info = lines[2].split(":")[1].strip()
    amount = lines[3].split(":")[1].strip().replace("USDT", "").strip()
    time_limit = lines[4].split(":")[1].strip().replace("hours", "").strip()

    deal_id = f"DEAL-{message.message_id}"

    deals[deal_id] = {
        "seller": f"@{seller}",
        "buyer": f"@{buyer}",
        "deal_info": deal_info,
        "amount": amount,
        "time_limit": time_limit,
        "seller_confirmed": False,
        "buyer_confirmed": False,
    }

    await message.reply(
        f"New Deal Created!\n\n"
        f"Seller: @{seller}\n"
        f"Buyer: @{buyer}\n"
        f"Deal Info: {deal_info}\n"
        f"Amount: {amount} USDT\n"
        f"Time: {time_limit} hours\n\n"
        "Waiting for both parties to confirm the deal.",
        reply_markup=deal_buttons(deal_id)
    )

@dp.callback_query(F.data.startswith("confirm:"))
async def handle_confirmation(callback: types.CallbackQuery):
    _, role, deal_id = callback.data.split(":")

    if deal_id not in deals:
        return await callback.answer("Deal not found!")

    deal = deals[deal_id]
    username = f"@{callback.from_user.username}"

    if role == "seller" and username != deal["seller"]:
        return await callback.answer("You are not the seller!")
    if role == "buyer" and username != deal["buyer"]:
        return await callback.answer("You are not the buyer!")

    if role == "seller":
        if deal["seller_confirmed"]:
            return await callback.answer("You already confirmed.")
        deals[deal_id]["seller_confirmed"] = True
        await bot.send_message(config.GROUP_ID, f"{deal['seller']} ❄ confirmed the deal. Waiting for {deal['buyer']} to confirm.")
    elif role == "buyer":
        if deal["buyer_confirmed"]:
            return await callback.answer("You already confirmed.")
        deals[deal_id]["buyer_confirmed"] = True
        await bot.send_message(config.GROUP_ID, f"{deal['buyer']} ❄ confirmed the deal. Waiting for {deal['seller']} to confirm.")

    if deal["seller_confirmed"] and deal["buyer_confirmed"]:
        pinned_message = await bot.send_message(
            config.GROUP_ID,
            f"✅ Deal On-Going\n"
            f"Deal ID: {deal_id}\n\n"
            f"Seller: {deal['seller']}\n"
            f"Buyer: {deal['buyer']}\n"
            f"Deal Info: {deal['deal_info']}\n"
            f"Amount: {deal['amount']} USDT\n"
            f"Time: {deal['time_limit']} hours"
        )
        await bot.pin_chat_message(config.GROUP_ID, pinned_message.message_id)
        await callback.message.edit_reply_markup(reply_markup=None)

    await callback.answer("Confirmation recorded.")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

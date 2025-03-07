import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import config

bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

deals = {}

def deal_buttons(deal_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Seller Confirm", callback_data=f"confirm:seller:{deal_id}")],
        [InlineKeyboardButton(text="✅ Buyer Confirm", callback_data=f"confirm:buyer:{deal_id}")]
    ])

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.reply("Welcome to Escrow Bot! Use /create to start a new deal (admin only).")

@dp.message(Command("create"))
async def create_deal(message: Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.reply("Only the admin can create deals.")
        return
    await message.reply(
        "Fill this form inside the group:\n\n"
        "Seller: @username\n"
        "Buyer: @username\n"
        "Deal Info: Item description\n"
        "Amount: 50 USDT\n"
        "Fee: 5 USDT\n"
        "Time: 24 hours"
    )

@dp.message(F.text.regexp(r"Seller:\s?@(\w+)\nBuyer:\s?@(\w+)\nDeal Info:\s?(.+)\nAmount:\s?(\d+)\s?USDT\nFee:\s?(\d+)\s?USDT\nTime:\s?(\d+)\s?hours"))
async def process_deal_form(message: Message):
    if message.chat.id != config.GROUP_ID:
        return  # Process only in the group.

    lines = message.text.strip().split("\n")
    seller = lines[0].split("@")[1].strip()
    buyer = lines[1].split("@")[1].strip()
    deal_info = lines[2].split(":")[1].strip()
    amount = lines[3].split(":")[1].strip().replace("USDT", "").strip()
    fee = lines[4].split(":")[1].strip().replace("USDT", "").strip()
    time_limit = lines[5].split(":")[1].strip().replace("hours", "").strip()

    deal_id = f"DEAL-{message.message_id}"

    deals[deal_id] = {
        "seller": f"@{seller}",
        "buyer": f"@{buyer}",
        "deal_info": deal_info,
        "amount": amount,
        "fee": fee,
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
        f"Fee: {fee} USDT\n"
        f"Time: {time_limit} hours\n\n"
        "Waiting for both parties to confirm.",
        reply_markup=deal_buttons(deal_id)
    )

@dp.callback_query(F.data.startswith("confirm:"))
async def handle_confirmation(callback: types.CallbackQuery):
    _, role, deal_id = callback.data.split(":")

    if deal_id not in deals:
        await callback.answer("Deal not found!")
        return

    deal = deals[deal_id]
    user = f"@{callback.from_user.username}"

    if role == "seller" and user != deal["seller"]:
        await callback.answer("You are not the seller!")
        return
    if role == "buyer" and user != deal["buyer"]:
        await callback.answer("You are not the buyer!")
        return

    if role == "seller":
        if deal["seller_confirmed"]:
            await callback.answer("Seller already confirmed.")
            return
        deal["seller_confirmed"] = True
        await bot.send_message(config.GROUP_ID, f"{deal['seller']} ❄ confirmed the deal. Waiting for {deal['buyer']} to confirm.")
    elif role == "buyer":
        if deal["buyer_confirmed"]:
            await callback.answer("Buyer already confirmed.")
            return
        deal["buyer_confirmed"] = True
        await bot.send_message(config.GROUP_ID, f"{deal['buyer']} ❄ confirmed the deal. Waiting for {deal['seller']} to confirm.")

    if deal["seller_confirmed"] and deal["buyer_confirmed"]:
        ongoing_message = (
            f"✅ Deal On-Going\n"
            f"Deal ID: {deal_id}\n\n"
            f"Seller: {deal['seller']}\n"
            f"Buyer: {deal['buyer']}\n"
            f"Deal Info: {deal['deal_info']}\n"
            f"Amount: {deal['amount']} USDT\n"
            f"Fee: {deal['fee']} USDT\n"
            f"Time: {deal['time_limit']} hours"
        )
        pinned_message = await bot.send_message(config.GROUP_ID, ongoing_message)
        await bot.pin_chat_message(config.GROUP_ID, pinned_message.message_id)

        await callback.message.edit_reply_markup(reply_markup=None)

    await callback.answer("Confirmation saved.")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

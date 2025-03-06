import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
import asyncio
from config import BOT_TOKEN, LOG_GROUP_ID, ADMINS

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

active_deals = {}

def generate_deal_id():
    import random
    return str(random.randint(100000000, 999999999))

@dp.message(Command("create"))
async def cmd_create(message: Message):
    form_text = (
        "Fill this form to start the deal:\n\n"
        "Seller :\n"
        "Buyer :\n"
        "Deal Info :\n"
        "Amount (In USDT) :\n"
        "Time To Complete : (in minutes)\n\n"
        "Reply to this message with the filled form."
    )
    await message.reply(form_text)

@dp.message(F.reply_to_message)
async def handle_form_reply(message: Message):
    original = message.reply_to_message.text
    if not original.startswith("Fill this form to start the deal:"):
        return

    deal_id = generate_deal_id()

    lines = message.text.strip().split("\n")
    try:
        seller = lines[0].split(":")[1].strip()
        buyer = lines[1].split(":")[1].strip()
        deal_info = lines[2].split(":")[1].strip()
        amount = lines[3].split(":")[1].strip()
        time_to_complete = lines[4].split(":")[1].strip()
    except Exception as e:
        await message.reply("Invalid format. Please fill all fields correctly.")
        return

    deal = {
        "seller": seller,
        "buyer": buyer,
        "deal_info": deal_info,
        "amount": amount,
        "time": time_to_complete,
        "confirmed": {"seller": False, "buyer": False},
        "fees_paid_by": None
    }
    active_deals[deal_id] = deal

    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"I am Seller ({seller})", callback_data=f"confirm:seller:{deal_id}")],
        [InlineKeyboardButton(text=f"I am Buyer ({buyer})", callback_data=f"confirm:buyer:{deal_id}")]
    ])

    deal_message = (
        f"Deal ID: <code>{deal_id}</code>\n"
        f"Seller: {seller}\n"
        f"Buyer: {buyer}\n"
        f"Deal Info: {deal_info}\n"
        f"Amount: {amount} USDT\n"
        f"Time To Complete: {time_to_complete} Minutes"
    )

    msg = await message.reply(f"New Deal Created!\n\n{deal_message}", reply_markup=confirm_keyboard)

    # Forward to log group
    await bot.send_message(LOG_GROUP_ID, f"New Deal Created!\n\n{deal_message}")

@dp.callback_query(F.data.startswith("confirm"))
async def confirm_role(call: CallbackQuery):
    _, role, deal_id = call.data.split(":")
    deal = active_deals.get(deal_id)

    if not deal:
        await call.answer("Deal not found.")
        return

    username = call.from_user.username
    expected = deal["seller" if role == "seller" else "buyer"]
    if f"@{username}" != expected:
        await call.answer(f"Only {expected} can confirm this.")
        return

    deal["confirmed"][role] = True
    await call.message.edit_text(f"{expected} confirmed as {role.capitalize()} for Deal ID {deal_id}")

    if deal["confirmed"]["seller"] and deal["confirmed"]["buyer"]:
        fees_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Split Fees", callback_data=f"fees:split:{deal_id}")],
            [InlineKeyboardButton(text="I will Pay Fees", callback_data=f"fees:one:{deal_id}")]
        ])
        await call.message.answer(f"Both parties confirmed! Who will pay the 2% fees for Deal ID {deal_id}?", reply_markup=fees_keyboard)

@dp.callback_query(F.data.startswith("fees"))
async def handle_fees(call: CallbackQuery):
    _, mode, deal_id = call.data.split(":")
    deal = active_deals.get(deal_id)

    if not deal:
        await call.answer("Deal not found.")
        return

    if mode == "split":
        deal["fees_paid_by"] = "split"
        text = "✅ Fees will be split equally."
    else:
        deal["fees_paid_by"] = "one"
        text = "✅ One party will cover all fees."

    await call.message.edit_text(f"Deal ID {deal_id}: {text}")

    ongoing_text = (
        f"On Going Deal - Deal ID: {deal_id}\n\n"
        f"Seller: {deal['seller']}\n"
        f"Buyer: {deal['buyer']}\n"
        f"Deal Info: {deal['deal_info']}\n"
        f"Amount (In USDT): {deal['amount']}\n"
        f"Time To Complete: {deal['time']} Minutes"
    )

    pinned_message = await call.message.answer(ongoing_text)
    await bot.pin_chat_message(call.message.chat.id, pinned_message.message_id)

    await bot.send_message(LOG_GROUP_ID, ongoing_text)

@dp.message(Command("dispute"))
async def cmd_dispute(message: Message):
    text = (
        "A dispute has been raised for an ongoing deal.\n"
        f"Chat link: <a href='https://t.me/{message.chat.username}'>Join Chat</a>\n\n"
        "Admins, please check and resolve."
    )
    for admin_id in ADMINS:
        await bot.send_message(admin_id, text, disable_web_page_preview=True)
    await message.reply("✅ Dispute raised. Admins have been notified.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

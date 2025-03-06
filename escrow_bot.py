import random
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.filters import Command

from config import TOKEN, LOGS_CHAT_ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, parse_mode=ParseMode.MARKDOWN)
dp = Dispatcher()

active_deals = {}


@dp.message(Command("create"))
async def create_command(message: types.Message):
    if message.chat.type not in ["supergroup", "group"]:
        await message.reply("This command only works inside a group.")
        return

    await message.reply(
        "Fill this form in this format:\n\n"
        "`Seller`: @username\n"
        "`Buyer`: @username\n"
        "`Deal Info`: Brief description\n"
        "`Amount`: 50 USDT\n"
        "`Time`: 24 hours"
    )


@dp.message(F.text.regexp(r"Seller:|Buyer:|Deal Info:|Amount:|Time:"))
async def form_handler(message: types.Message):
    if message.chat.type not in ["supergroup", "group"]:
        return

    lines = message.text.splitlines()
    if not all(any(line.startswith(f"{key}:") for line in lines) for key in ["Seller", "Buyer", "Deal Info", "Amount", "Time"]):
        return

    data = {}
    for line in lines:
        if ": " in line:
            key, value = line.split(": ", 1)
            data[key.strip()] = value.strip()

    deal_id = str(random.randint(100000, 999999))

    active_deals[deal_id] = {
        "seller": data["Seller"],
        "buyer": data["Buyer"],
        "info": data["Deal Info"],
        "amount": data["Amount"],
        "time": data["Time"],
        "confirmed": {"seller": False, "buyer": False},
        "fees": None,
        "message_id": None,
    }

    text = (
        f"✅ *Form Received!*\n\n"
        f"*Seller*: {data['Seller']}\n"
        f"*Buyer*: {data['Buyer']}\n"
        f"*Deal Info*: {data['Deal Info']}\n"
        f"*Amount*: {data['Amount']}\n"
        f"*Time To Complete*: {data['Time']}\n\n"
        "*Both parties need to confirm their roles:*"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"{data['Seller']} ❄ Confirm Role (Seller)", callback_data=f"confirm_{deal_id}_seller")],
        [InlineKeyboardButton(f"{data['Buyer']} ❄ Confirm Role (Buyer)", callback_data=f"confirm_{deal_id}_buyer")]
    ])

    sent_message = await message.reply(text, reply_markup=keyboard)
    active_deals[deal_id]["message_id"] = sent_message.message_id

    await bot.send_message(LOGS_CHAT_ID, f"New Deal Created! Deal ID: {deal_id}")


@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_callback(callback: types.CallbackQuery):
    _, deal_id, role = callback.data.split("_")

    if deal_id not in active_deals:
        await callback.answer("This deal no longer exists.")
        return

    deal = active_deals[deal_id]
    username = f"@{callback.from_user.username}"

    if role not in ["seller", "buyer"]:
        await callback.answer("Invalid role.")
        return

    if (role == "seller" and username != deal["seller"]) or (role == "buyer" and username != deal["buyer"]):
        await callback.answer("Only the correct person can confirm this role.")
        return

    if deal["confirmed"][role]:
        await callback.answer("You already confirmed.")
        return

    deal["confirmed"][role] = True
    await callback.message.chat.send_message(f"✅ {username} confirmed the deal as {role.capitalize()}.\nWaiting for the other party to confirm!")

    if deal["confirmed"]["seller"] and deal["confirmed"]["buyer"]:
        form_text = (
            f"✅ *Form Received!*\n\n"
            f"*Seller*: {deal['seller']}\n"
            f"*Buyer*: {deal['buyer']}\n"
            f"*Deal Info*: {deal['info']}\n"
            f"*Amount*: {deal['amount']}\n"
            f"*Time To Complete*: {deal['time']}\n\n"
            f"✅ Deal Confirmed — *Ongoing Deal (ID: {deal_id})*"
        )

        await bot.edit_message_text(form_text, callback.message.chat.id, deal["message_id"])
        await bot.pin_chat_message(callback.message.chat.id, deal["message_id"])

        fee_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("Split (1% each)", callback_data=f"fees_{deal_id}_split")],
            [InlineKeyboardButton("I Pay All (2%)", callback_data=f"fees_{deal_id}_mine")]
        ])
        await callback.message.chat.send_message("✅ Both confirmed! Now, choose who pays the fees:", reply_markup=fee_keyboard)

    await callback.answer()


@dp.callback_query(F.data.startswith("fees_"))
async def fees_callback(callback: types.CallbackQuery):
    _, deal_id, fee_choice = callback.data.split("_")

    if deal_id not in active_deals:
        await callback.answer("This deal no longer exists.")
        return

    deal = active_deals[deal_id]
    username = f"@{callback.from_user.username}"

    if username not in [deal["seller"], deal["buyer"]]:
        await callback.answer("Only Buyer or Seller can choose the fees.")
        return

    if deal["fees"] is not None:
        await callback.answer("Fees already decided.")
        return

    deal["fees"] = fee_choice

    if fee_choice == "split":
        await callback.message.edit_text("✅ Both confirmed! Fees will be split: *1% each party*.")
    else:
        payer = "Seller" if username == deal["seller"] else "Buyer"
        await callback.message.edit_text(f"✅ Both confirmed! {payer} will pay the full *2% fee*.")

    await callback.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

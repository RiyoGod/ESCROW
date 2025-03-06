import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
import asyncio
import logging
from config import TOKEN, LOGS_CHAT_ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, parse_mode=ParseMode.MARKDOWN_V2)
dp = Dispatcher()

active_deals = {}


@dp.message(commands=["create"])
async def create_command(message: types.Message):
    if message.chat.type != "supergroup" and message.chat.type != "group":
        return await message.reply("This command only works inside a group.")

    await message.reply(
        "Fill this form in format:\n\n"
        "`Seller`: @username\n"
        "`Buyer`: @username\n"
        "`Deal Info`: Brief description\n"
        "`Amount`: 50 USDT\n"
        "`Time`: 24 hours"
    )


@dp.message()
async def form_handler(message: types.Message):
    if message.chat.type != "supergroup" and message.chat.type != "group":
        return

    if not all(x in message.text for x in ["Seller:", "Buyer:", "Deal Info:", "Amount:", "Time:"]):
        return

    data = {}
    for line in message.text.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            data[key.strip()] = value.strip()

    deal_id = str(random.randint(100000, 999999))

    active_deals[deal_id] = {
        "seller": data.get("Seller"),
        "buyer": data.get("Buyer"),
        "info": data.get("Deal Info"),
        "amount": data.get("Amount"),
        "time": data.get("Time"),
        "confirmed": {"seller": False, "buyer": False},
        "fees": None,
        "message_id": None
    }

    text = (
        f"✅ *Form Received!*\n\n"
        f"*Seller*: {data.get('Seller')}\n"
        f"*Buyer*: {data.get('Buyer')}\n"
        f"*Deal Info*: {data.get('Deal Info')}\n"
        f"*Amount*: {data.get('Amount')}\n"
        f"*Time To Complete*: {data.get('Time')}\n\n"
        "*Both of you confirm your roles:*"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{data.get('Seller')} ❄ Confirm Role (Seller)", callback_data=f"confirm_{deal_id}_seller")],
        [InlineKeyboardButton(text=f"{data.get('Buyer')} ❄ Confirm Role (Buyer)", callback_data=f"confirm_{deal_id}_buyer")]
    ])

    sent = await message.reply(text, reply_markup=keyboard)

    active_deals[deal_id]["message_id"] = sent.message_id

    await bot.send_message(LOGS_CHAT_ID, f"New Deal Created! Deal ID: {deal_id}")


@dp.callback_query(lambda c: c.data.startswith("confirm_"))
async def confirm_callback(callback: types.CallbackQuery):
    _, deal_id, role = callback.data.split("_")

    if deal_id not in active_deals:
        return await callback.answer("This deal no longer exists.")

    deal = active_deals[deal_id]
    username = callback.from_user.username

    if role not in ["seller", "buyer"]:
        return await callback.answer("Invalid role.")

    if (role == "seller" and f"@{username}" != deal["seller"]) or (role == "buyer" and f"@{username}" != deal["buyer"]):
        return await callback.answer("Only the correct person can confirm this role.")

    if deal["confirmed"][role]:
        return await callback.answer("You already confirmed.")

    deal["confirmed"][role] = True

    await callback.message.chat.send_message(
        f"✅ @{username} confirmed the deal as *{role.capitalize()}*.\n"
        f"Waiting for the other party to confirm!"
    )

    if deal["confirmed"]["seller"] and deal["confirmed"]["buyer"]:
        # Both confirmed — Edit main message
        text = (
            f"✅ *Form Received!*\n\n"
            f"*Seller*: {deal['seller']}\n"
            f"*Buyer*: {deal['buyer']}\n"
            f"*Deal Info*: {deal['info']}\n"
            f"*Amount*: {deal['amount']}\n"
            f"*Time To Complete*: {deal['time']}\n\n"
            f"✅ Deal Confirmed — *Ongoing Deal (ID: {deal_id})*"
        )
        await bot.edit_message_text(text, callback.message.chat.id, deal["message_id"])

        await bot.pin_chat_message(callback.message.chat.id, deal["message_id"])

        # Send fees choice message
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Split (Each 1%)", callback_data=f"fees_{deal_id}_split")],
            [InlineKeyboardButton(text="Mine (I pay 2%)", callback_data=f"fees_{deal_id}_mine")]
        ])
        await callback.message.chat.send_message(
            "✅ Both confirmed! Choose who pays the fees:",
            reply_markup=keyboard
        )

    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("fees_"))
async def fees_callback(callback: types.CallbackQuery):
    _, deal_id, fee_type = callback.data.split("_")

    if deal_id not in active_deals:
        return await callback.answer("This deal no longer exists.")

    deal = active_deals[deal_id]
    username = callback.from_user.username

    if username not in [deal["seller"][1:], deal["buyer"][1:]]:
        return await callback.answer("Only buyer or seller can choose fees.")

    if deal["fees"] is not None:
        return await callback.answer("Fees option already chosen.")

    deal["fees"] = fee_type

    if fee_type == "split":
        await callback.message.edit_text(
            f"✅ Both confirmed!\n\n✅ Fees will be *split*: Each pays 1%."
        )
    else:
        payer = "Seller" if f"@{username}" == deal["seller"] else "Buyer"
        await callback.message.edit_text(
            f"✅ Both confirmed!\n\n✅ {payer} chose to pay full *2% fees*."
        )

    await callback.answer()


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

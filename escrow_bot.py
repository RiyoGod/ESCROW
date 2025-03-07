import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import Command
from config import TOKEN, LOGS_CHAT_ID, ADMINS, ESCROW_FEES_PERCENTAGE

bot = Bot(token=TOKEN, parse_mode=ParseMode.MARKDOWN)
dp = Dispatcher()

deals = {}

@dp.message(Command("create"))
async def create_command(message: types.Message):
    if message.chat.type == "private":
        await message.reply("❌ *This command only works inside a group.*")
        return

    deal_id = f"ESCROW-{message.message_id}"
    deals[deal_id] = {
        "seller": None,
        "buyer": None,
        "info": None,
        "amount": None,
        "time": None,
        "confirmed": {"seller": False, "buyer": False},
        "fees": None,
        "pinned_message_id": None,
    }

    await message.reply(
        "**Please fill the form below (reply this message):**\n\n"
        "`Seller @username`\n"
        "`Buyer @username`\n"
        "`Deal Info`\n"
        "`Amount (USDT)`\n"
        "`Time To Complete`\n\n"
        "⚠️ Reply this message with the filled form."
    )

@dp.message()
async def capture_form(message: types.Message):
    if not message.reply_to_message or "Please fill the form below" not in message.reply_to_message.text:
        return

    deal_id = f"ESCROW-{message.reply_to_message.message_id}"
    if deal_id not in deals:
        return

    try:
        lines = message.text.split("\n")
        deals[deal_id]["seller"] = lines[0].split()[1]
        deals[deal_id]["buyer"] = lines[1].split()[1]
        deals[deal_id]["info"] = lines[2].split(":", 1)[1].strip()
        deals[deal_id]["amount"] = lines[3].split(":", 1)[1].strip()
        deals[deal_id]["time"] = lines[4].split(":", 1)[1].strip()
    except IndexError:
        await message.reply("❌ Invalid format. Please fill all lines correctly.")
        return

    seller_button = InlineKeyboardButton(f"{deals[deal_id]['seller']} ❄ Confirm ❄", callback_data=f"confirm_seller_{deal_id}")
    buyer_button = InlineKeyboardButton(f"{deals[deal_id]['buyer']} ❄ Confirm ❄", callback_data=f"confirm_buyer_{deal_id}")
    markup = InlineKeyboardMarkup(inline_keyboard=[[seller_button], [buyer_button]])

    text = (
        f"✅ *Form Received!*\n\n"
        f"`Seller`: {deals[deal_id]['seller']}\n"
        f"`Buyer`: {deals[deal_id]['buyer']}\n"
        f"`Deal Info`: {deals[deal_id]['info']}\n"
        f"`Amount`: {deals[deal_id]['amount']} USDT\n"
        f"`Time To Complete`: {deals[deal_id]['time']}\n\n"
        "*Both parties confirm your roles.*"
    )

    msg = await message.reply(text, reply_markup=markup)
    deals[deal_id]["pinned_message_id"] = msg.message_id

@dp.callback_query()
async def confirm_callback(callback: types.CallbackQuery):
    role, deal_id = callback.data.split("_")[1:3]
    if deal_id not in deals:
        await callback.answer("This deal no longer exists.")
        return

    if deals[deal_id]["confirmed"][role]:
        await callback.answer(f"{role.capitalize()} already confirmed.")
        return

    deals[deal_id]["confirmed"][role] = True
    await callback.answer(f"{role.capitalize()} confirmed.")

    if all(deals[deal_id]["confirmed"].values()):
        fees_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("Mine (I pay all fees)", callback_data=f"fees_mine_{deal_id}")],
            [InlineKeyboardButton("Split (We both pay)", callback_data=f"fees_split_{deal_id}")]
        ])
        await callback.message.reply("✅ Both confirmed! Now choose who pays the escrow fees.", reply_markup=fees_markup)

        log_text = (
            "**New Deal Created**\n\n"
            f"`Seller`: {deals[deal_id]['seller']}\n"
            f"`Buyer`: {deals[deal_id]['buyer']}\n"
            f"`Deal Info`: {deals[deal_id]['info']}\n"
            f"`Amount`: {deals[deal_id]['amount']} USDT\n"
            f"`Time`: {deals[deal_id]['time']}\n"
            f"`Deal ID`: {deal_id}"
        )
        await bot.send_message(LOGS_CHAT_ID, log_text)

    else:
        await callback.message.reply(f"✅ {role.capitalize()} confirmed. Waiting for the other party.")

@dp.callback_query()
async def fees_callback(callback: types.CallbackQuery):
    fees_type, deal_id = callback.data.split("_")[1:3]
    if deal_id not in deals or deals[deal_id]["fees"]:
        await callback.answer("This fee option is no longer available.")
        return

    deals[deal_id]["fees"] = fees_type

    if fees_type == "mine":
        payer = deals[deal_id]["seller"] if deals[deal_id]["confirmed"]["seller"] else deals[deal_id]["buyer"]
        fees_text = f"✅ {payer} chose to pay all the fees."
    else:
        fees_text = "✅ Fees will be split, both parties pay 1% each."

    await callback.message.edit_text(fees_text)

    pin_text = (
        f"`Seller`: {deals[deal_id]['seller']}\n"
        f"`Buyer`: {deals[deal_id]['buyer']}\n"
        f"`Deal Info`: {deals[deal_id]['info']}\n"
        f"`Amount`: {deals[deal_id]['amount']} USDT\n"
        f"`Time`: {deals[deal_id]['time']}\n\n"
        f"**Status:** __On Going Deal__\n"
        f"**Escrow ID:** `{deal_id}`"
    )

    cancel_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Request Refund/Cancel", callback_data=f"cancel_{deal_id}")]
    ])
    await callback.message.chat.pin_message(deals[deal_id]["pinned_message_id"])
    await bot.edit_message_text(pin_text, callback.message.chat.id, deals[deal_id]["pinned_message_id"], reply_markup=cancel_markup)

@dp.callback_query()
async def cancel_request(callback: types.CallbackQuery):
    _, deal_id = callback.data.split("_")
    if deal_id not in deals:
        await callback.answer("This deal no longer exists.")
        return

    user = callback.from_user.username
    cancel_text = f"⚠️ @{user} requested to cancel the deal. Waiting for the other party to agree."

    cancel_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Agree to Cancel", callback_data=f"agreecancel_{deal_id}")]
    ])

    await callback.message.reply(cancel_text, reply_markup=cancel_markup)

@dp.callback_query()
async def agree_cancel(callback: types.CallbackQuery):
    _, deal_id = callback.data.split("_")
    if deal_id not in deals:
        await callback.answer("This deal no longer exists.")
        return

    await callback.message.reply("✅ Both parties agreed. Deal cancelled.")
    deals.pop(deal_id, None)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

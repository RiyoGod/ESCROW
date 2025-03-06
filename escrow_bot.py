import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import TOKEN, LOGS_CHAT_ID, ADMINS

bot = Bot(token=TOKEN, parse_mode=ParseMode.MARKDOWN)
dp = Dispatcher()

active_deals = {}

@dp.message(Command("create"))
async def create_command(message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        return await message.reply("This command only works inside a group.")
    
    form_text = (
        "Fill the deal form in this format:\n\n"
        "*Seller:* @username\n"
        "*Buyer:* @username\n"
        "*Deal Info:* (short details)\n"
        "*Amount (In USDT):* amount\n"
        "*Time To Complete:* time\n\n"
        "Copy, fill it, and send it here."
    )
    await message.reply(form_text)

@dp.message()
async def handle_form(message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        return

    lines = message.text.strip().split("\n")
    if len(lines) < 5:
        return

    try:
        seller = lines[0].split(":")[1].strip()
        buyer = lines[1].split(":")[1].strip()
        deal_info = lines[2].split(":")[1].strip()
        amount = lines[3].split(":")[1].strip()
        time_to_complete = lines[4].split(":")[1].strip()
    except IndexError:
        return

    if not seller.startswith("@") or not buyer.startswith("@"):
        return

    deal_id = f"DEAL-{message.chat.id}-{message.message_id}"
    active_deals[deal_id] = {
        "seller": seller,
        "buyer": buyer,
        "confirmed": {"seller": False, "buyer": False},
        "fees": None
    }

    form_text = (
        "✅ Form Received!\n\n"
        f"*Seller:* {seller}\n"
        f"*Buyer:* {buyer}\n"
        f"*Deal Info:* {deal_info}\n"
        f"*Amount:* {amount} USDT\n"
        f"*Time to Complete:* {time_to_complete} hours\n\n"
        "Both of you confirm your roles below:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{seller[1:]} ❄ {seller} ❄", callback_data=f"confirm_{deal_id}_seller")],
        [InlineKeyboardButton(text=f"{buyer[1:]} ❄ {buyer} ❄", callback_data=f"confirm_{deal_id}_buyer")]
    ])

    sent_message = await message.reply(form_text, reply_markup=keyboard)
    await bot.send_message(LOGS_CHAT_ID, form_text)

@dp.callback_query()
async def confirm_callback(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    if len(parts) != 3:
        return

    action, deal_id, role = parts

    if deal_id not in active_deals:
        return await callback.answer("This deal no longer exists.")

    deal = active_deals[deal_id]
    username = callback.from_user.username

    if role == "seller" and username != deal["seller"][1:]:
        return await callback.answer("Only the seller can confirm.")
    if role == "buyer" and username != deal["buyer"][1:]:
        return await callback.answer("Only the buyer can confirm.")

    if deal["confirmed"][role]:
        return await callback.answer("You already confirmed.")

    deal["confirmed"][role] = True

    text = callback.message.text + f"\n✅ {role.capitalize()} Confirmed!"

    if deal["confirmed"]["seller"] and deal["confirmed"]["buyer"]:
        text += "\n\n✅ Both Confirmed! Choose who pays the fees:"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Split (Both Pay 1% Each)", callback_data=f"fees_{deal_id}_split")],
            [InlineKeyboardButton(text="Mine (I Pay Full 2%)", callback_data=f"fees_{deal_id}_mine")]
        ])
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.message.edit_text(text, reply_markup=callback.message.reply_markup)

    await callback.answer()

@dp.callback_query()
async def fees_callback(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    if len(parts) != 3:
        return

    action, deal_id, fees_type = parts

    if deal_id not in active_deals:
        return await callback.answer("This deal no longer exists.")

    deal = active_deals[deal_id]
    username = callback.from_user.username

    if username not in [deal["seller"][1:], deal["buyer"][1:]]:
        return await callback.answer("Only seller or buyer can choose fees.")

    if deal["fees"] is not None:
        return await callback.answer("Fees already chosen.")

    deal["fees"] = fees_type

    if fees_type == "split":
        text = callback.message.text + "\n\n✅ Fees Split! Each pays 1%."
    else:
        payer = "Seller" if username == deal["seller"][1:] else "Buyer"
        text = callback.message.text + f"\n\n✅ {payer} chose to pay full 2% fees."

    await callback.message.edit_text(text + "\n\n🚀 *On Going Deal!*", reply_markup=None)
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

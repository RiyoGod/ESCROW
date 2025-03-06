import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import TOKEN, LOGS_CHAT_ID, ADMINS

bot = Bot(token=TOKEN, parse_mode=ParseMode.MARKDOWN_V2)
dp = Dispatcher()

active_deals = {}

def escape_md_v2(text: str) -> str:
    """Escape text for Markdown v2."""
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

@dp.message(commands=["create"])
async def create_command(message: types.Message):
    await message.reply(
        "✍️ Fill the form below and send it back to me:\n\n"
        "`Seller :`\n"
        "`Buyer :`\n"
        "`Deal Info :`\n"
        "`Amount (In USDT) :`\n"
        "`Time To Complete :`"
    )

@dp.message()
async def form_handler(message: types.Message):
    if not (message.text.startswith("Seller :") and "Buyer :" in message.text):
        return

    form_lines = message.text.strip().split("\n")
    if len(form_lines) < 5:
        await message.reply("Invalid form format! Please try again.")
        return

    seller = form_lines[0].replace("Seller :", "").strip()
    buyer = form_lines[1].replace("Buyer :", "").strip()
    deal_info = form_lines[2].replace("Deal Info :", "").strip()
    amount = form_lines[3].replace("Amount (In USDT) :", "").strip()
    time = form_lines[4].replace("Time To Complete :", "").strip()

    if not (seller.startswith("@") and buyer.startswith("@")):
        await message.reply("Both seller and buyer must be valid usernames starting with '@'.")
        return

    deal_id = str(message.message_id)
    active_deals[deal_id] = {
        "seller": seller,
        "buyer": buyer,
        "confirmed": {"seller": False, "buyer": False},
        "fees": None,
        "form": message.text
    }

    form_text = (
        f"✅ *Form received!*\n\n"
        f"Seller : {escape_md_v2(seller)}\n"
        f"Buyer : {escape_md_v2(buyer)}\n"
        f"Deal Info : {escape_md_v2(deal_info)}\n"
        f"Amount \\(In USDT\\) : {escape_md_v2(amount)}\n"
        f"Time To Complete : {escape_md_v2(time)}\n\n"
        "Both of you confirm your roles below:"
    )

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{escape_md_v2(seller)} \\(Seller\\)", callback_data=f"confirm_{deal_id}_seller")],
        [InlineKeyboardButton(text=f"{escape_md_v2(buyer)} \\(Buyer\\)", callback_data=f"confirm_{deal_id}_buyer")]
    ])

    # Forward form to logs group
    await bot.send_message(LOGS_CHAT_ID, f"New deal created:\n\n{escape_md_v2(message.text)}")

    await message.reply(form_text, reply_markup=buttons)

@dp.callback_query(lambda c: c.data.startswith("confirm_"))
async def confirm_role(callback: types.CallbackQuery):
    _, deal_id, role = callback.data.split("_")
    deal = active_deals.get(deal_id)

    if not deal:
        await callback.answer("Deal not found or expired.")
        return

    user = callback.from_user.username
    expected = deal[role]

    if f"@{user}" != expected:
        await callback.answer("You are not allowed to confirm this role.")
        return

    deal["confirmed"][role] = True

    if all(deal["confirmed"].values()):
        await handle_fees_selection(callback.message, deal_id)
    else:
        await callback.message.edit_text(
            callback.message.text + f"\n\n✅ {role.capitalize()} confirmed by {expected}"
        )
        await callback.answer("Role confirmed!")

async def handle_fees_selection(message: types.Message, deal_id: str):
    deal = active_deals[deal_id]

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{escape_md_v2(deal['seller'])} \\- I Pay Full", callback_data=f"fees_{deal_id}_seller")],
        [InlineKeyboardButton(text=f"{escape_md_v2(deal['buyer'])} \\- I Pay Full", callback_data=f"fees_{deal_id}_buyer")],
        [InlineKeyboardButton(text="Split 50/50", callback_data=f"fees_{deal_id}_split")]
    ])

    await message.edit_text(
        message.text + "\n\n💰 Now choose who pays the 2% escrow fees:",
        reply_markup=buttons
    )

@dp.callback_query(lambda c: c.data.startswith("fees_"))
async def confirm_fees(callback: types.CallbackQuery):
    _, deal_id, fees_choice = callback.data.split("_")
    deal = active_deals.get(deal_id)

    if not deal:
        await callback.answer("Deal not found or expired.")
        return

    user = callback.from_user.username
    if f"@{user}" not in [deal["seller"], deal["buyer"]]:
        await callback.answer("You are not part of this deal.")
        return

    if deal["fees"]:
        await callback.answer("Fees have already been selected.")
        return

    if fees_choice == "split":
        deal["fees"] = "split"
        fees_text = "✅ Both of you will split the fees 50/50."
    else:
        deal["fees"] = fees_choice
        role = "Seller" if fees_choice == "seller" else "Buyer"
        fees_text = f"✅ {role} ({deal[fees_choice]}) will pay the full fees."

    await callback.message.edit_text(
        callback.message.text + f"\n\n{fees_text}\n\n✅ Deal confirmed & pinned as *Ongoing Deal*"
    )

    await callback.answer("Fees confirmed!")

    # Pin this deal message
    chat_id = callback.message.chat.id
    await bot.pin_chat_message(chat_id, callback.message.message_id)

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))

import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import TOKEN, LOGS_CHAT_ID, ADMINS

bot = Bot(token=TOKEN, parse_mode=ParseMode.MARKDOWN_V2)
dp = Dispatcher()

active_deals = {}

def escape_markdown_v2(text):
    escape_chars = r"*_[]()~`>#+-=|{}.!<>"
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

@dp.message(Command("create"))
async def create_command(message: Message):
    if not message.chat.type in ["group", "supergroup"]:
        return await message.reply("This command only works inside a group.")
    
    deal_form = (
        "Fill the deal form in this format:\n\n"
        "`Seller : @username`\n"
        "`Buyer : @username`\n"
        "`Deal Info : (short details)`\n"
        "`Amount (In USDT) : amount`\n"
        "`Time To Complete : time`\n\n"
        "Copy the format, fill it, and send it in this group."
    )
    await message.reply(deal_form)

@dp.message()
async def handle_form(message: Message):
    if not message.text or not message.chat.type in ["group", "supergroup"]:
        return

    lines = message.text.split("\n")
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

    if not (seller.startswith("@") and buyer.startswith("@")):
        return

    deal_id = f"DEAL-{message.chat.id}-{message.message_id}"

    active_deals[deal_id] = {
        "seller": seller,
        "buyer": buyer,
        "amount": amount,
        "time": time_to_complete,
        "confirmed": {"seller": False, "buyer": False},
        "fees": None,
        "pinned_message_id": None
    }

    form_text = (
        f"✅ Form Received!\n\n"
        f"*Seller:* {escape_markdown_v2(seller)}\n"
        f"*Buyer:* {escape_markdown_v2(buyer)}\n"
        f"*Deal Info:* {escape_markdown_v2(deal_info)}\n"
        f"*Amount:* {escape_markdown_v2(amount)} USDT\n"
        f"*Time to Complete:* {escape_markdown_v2(time_to_complete)} hours\n\n"
        f"Both of you confirm your roles by clicking the buttons below:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{seller[1:]} ❄ {seller} ❄", callback_data=f"confirm_{deal_id}_seller")],
        [InlineKeyboardButton(text=f"{buyer[1:]} ❄ {buyer} ❄", callback_data=f"confirm_{deal_id}_buyer")]
    ])

    sent_message = await message.reply(form_text, reply_markup=keyboard)

    # Log group forward
    await bot.send_message(LOGS_CHAT_ID, form_text)

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    data = callback.data
    if not data.startswith("confirm_") and not data.startswith("fees_"):
        return

    parts = data.split("_")
    action, deal_id, role = parts[0], parts[1], parts[2]

    if deal_id not in active_deals:
        return await callback.answer("This deal is no longer active.")

    deal = active_deals[deal_id]
    if role == "seller" and callback.from_user.username != deal["seller"][1:]:
        return await callback.answer("Only the seller can confirm this.")
    if role == "buyer" and callback.from_user.username != deal["buyer"][1:]:
        return await callback.answer("Only the buyer can confirm this.")

    if deal["confirmed"][role]:
        return await callback.answer("You already confirmed.")

    deal["confirmed"][role] = True

    if deal["confirmed"]["seller"] and deal["confirmed"]["buyer"]:
        # Both confirmed
        fees_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Split (Both Pay 1% Each)", callback_data=f"fees_{deal_id}_split")],
            [InlineKeyboardButton(text="Mine (I Pay Full 2%)", callback_data=f"fees_{deal_id}_mine")]
        ])
        await callback.message.edit_text(callback.message.text + "\n\n✅ Both Confirmed! Choose who pays the fees:", reply_markup=fees_keyboard)
    else:
        await callback.message.edit_text(callback.message.text + f"\n\n✅ {role.capitalize()} Confirmed!")

    await callback.answer()

@dp.callback_query()
async def fees_handler(callback: types.CallbackQuery):
    data = callback.data
    if not data.startswith("fees_"):
        return

    parts = data.split("_")
    _, deal_id, fees_type = parts

    if deal_id not in active_deals:
        return await callback.answer("This deal is no longer active.")

    deal = active_deals[deal_id]
    if callback.from_user.username not in (deal["seller"][1:], deal["buyer"][1:]):
        return await callback.answer("Only the seller or buyer can choose fees.")

    if deal["fees"] is not None:
        return await callback.answer("Fees choice already locked.")

    deal["fees"] = fees_type

    if fees_type == "split":
        await callback.message.edit_text(callback.message.text + "\n\n✅ Fees split 1% each!")
    else:
        payer = "Seller" if callback.from_user.username == deal["seller"][1:] else "Buyer"
        await callback.message.edit_text(callback.message.text + f"\n\n✅ {payer} chose to pay full 2% fees!")

    # Remove buttons after selection
    await callback.message.edit_reply_markup(reply_markup=None)

    # Pin the message with "Ongoing Deal"
    pinned_text = callback.message.text + "\n\n🚀 *On Going Deal!*"
    pinned_message = await callback.message.edit_text(pinned_text)
    deal["pinned_message_id"] = pinned_message.message_id

    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

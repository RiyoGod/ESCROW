import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN, LOGS_CHAT_ID, ADMINS

bot = Bot(token=TOKEN, parse_mode=ParseMode.MARKDOWN_V2)
dp = Dispatcher()

# Deal data storage (temporary — will reset when bot restarts)
active_deals = {}

# Create command — must be inside group
@dp.message(Command("create"))
async def create_command(message: types.Message):
    if message.chat.type != "supergroup":
        await message.reply("This command only works inside a group.")
        return

    await message.reply(
        "*Fill the deal form and send it in this format:*"
        "\n\nSeller: @username\nBuyer: @username\nDeal Info: Short description\nAmount (in USDT): Amount\nTime to Complete: Time in hours"
    )

# Form detection
@dp.message()
async def process_form(message: types.Message):
    if message.chat.type != "supergroup":
        return

    if not (message.text.startswith("Seller:") and "Buyer:" in message.text and "Deal Info:" in message.text):
        return

    lines = message.text.strip().split("\n")
    try:
        seller = lines[0].split(":")[1].strip()
        buyer = lines[1].split(":")[1].strip()
        deal_info = lines[2].split(":")[1].strip()
        amount = lines[3].split(":")[1].strip()
        time_to_complete = lines[4].split(":")[1].strip()
    except IndexError:
        await message.reply("❌ *Invalid format.* Please follow the correct format.")
        return

    deal_id = f"DEAL-{message.message_id}"

    active_deals[deal_id] = {
        "seller": seller,
        "buyer": buyer,
        "info": deal_info,
        "amount": amount,
        "time": time_to_complete,
        "confirmed": {"seller": False, "buyer": False},
        "fees": None
    }

    form_text = (
        f"✅ *Form Received!* \n\n"
        f"*Seller:* {seller}\n"
        f"*Buyer:* {buyer}\n"
        f"*Deal Info:* {deal_info}\n"
        f"*Amount:* {amount} USDT\n"
        f"*Time to Complete:* {time_to_complete} hours\n\n"
        "⚠️ *Both of you confirm your roles:*"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Confirm Seller ({seller})", callback_data=f"confirm_{deal_id}_seller")],
        [InlineKeyboardButton(text=f"Confirm Buyer ({buyer})", callback_data=f"confirm_{deal_id}_buyer")]
    ])

    sent = await message.reply(form_text, reply_markup=keyboard)
    active_deals[deal_id]["message_id"] = sent.message_id

    # Forward to logs group
    await bot.send_message(
        LOGS_CHAT_ID,
        f"New deal form submitted in {message.chat.title}\n\n{form_text}"
    )

# Confirm role handler
@dp.callback_query()
async def confirm_role(callback: types.CallbackQuery):
    data = callback.data.split("_")
    if len(data) < 3:
        return

    action, deal_id, role = data
    if deal_id not in active_deals:
        await callback.answer("This deal no longer exists.")
        return

    deal = active_deals[deal_id]
    user = f"@{callback.from_user.username}"

    if role == "seller" and user != deal['seller']:
        await callback.answer("Only the seller can confirm this.")
        return
    elif role == "buyer" and user != deal['buyer']:
        await callback.answer("Only the buyer can confirm this.")
        return

    deal["confirmed"][role] = True
    await callback.message.edit_reply_markup(reply_markup=update_confirm_buttons(deal_id))

    if deal["confirmed"]["seller"] and deal["confirmed"]["buyer"]:
        await ask_for_fees(callback.message, deal_id)

# Update confirm buttons after one person confirms
def update_confirm_buttons(deal_id):
    deal = active_deals[deal_id]
    buttons = []

    if not deal["confirmed"]["seller"]:
        buttons.append([InlineKeyboardButton(text=f"Confirm Seller ({deal['seller']})", callback_data=f"confirm_{deal_id}_seller")])
    if not deal["confirmed"]["buyer"]:
        buttons.append([InlineKeyboardButton(text=f"Confirm Buyer ({deal['buyer']})", callback_data=f"confirm_{deal_id}_buyer")])

    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None

# Ask who pays the fee
async def ask_for_fees(message: types.Message, deal_id):
    deal = active_deals[deal_id]
    form_text = (
        f"✅ *Form Received!* \n\n"
        f"*Seller:* {deal['seller']}\n"
        f"*Buyer:* {deal['buyer']}\n"
        f"*Deal Info:* {deal['info']}\n"
        f"*Amount:* {deal['amount']} USDT\n"
        f"*Time to Complete:* {deal['time']} hours\n\n"
        "✅ *Both confirmed! Now choose who pays the 2% escrow fee:*"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="I’ll Pay Full Fees", callback_data=f"fees_{deal_id}_mine")],
        [InlineKeyboardButton(text="Split 50/50", callback_data=f"fees_{deal_id}_split")]
    ])
    await message.edit_text(form_text, reply_markup=keyboard)

# Handle fee choice
@dp.callback_query()
async def fee_choice(callback: types.CallbackQuery):
    data = callback.data.split("_")
    if len(data) < 3:
        return

    action, deal_id, fee_type = data
    if deal_id not in active_deals:
        await callback.answer("This deal no longer exists.")
        return

    deal = active_deals[deal_id]
    user = f"@{callback.from_user.username}"

    if user not in [deal['seller'], deal['buyer']]:
        await callback.answer("Only the seller or buyer can choose fees.")
        return

    if deal["fees"]:
        await callback.answer("Fees have already been set.")
        return

    deal["fees"] = fee_type

    if fee_type == "mine":
        fee_text = f"{user} chose to pay the full fees."
    else:
        fee_text = f"{user} chose to split the fees 50/50."

    await callback.message.edit_text(
        f"✅ *Deal Confirmed & Pinned!*\n\n"
        f"*Seller:* {deal['seller']}\n"
        f"*Buyer:* {deal['buyer']}\n"
        f"*Deal Info:* {deal['info']}\n"
        f"*Amount:* {deal['amount']} USDT\n"
        f"*Time to Complete:* {deal['time']} hours\n\n"
        f"💰 *Fee Option:* {fee_text}\n\n"
        "*Deal Status:* Ongoing"
    )

    await bot.pin_chat_message(callback.message.chat.id, callback.message.message_id)

    await bot.send_message(
        LOGS_CHAT_ID,
        f"✅ Deal Confirmed!\n\n"
        f"*Seller:* {deal['seller']}\n"
        f"*Buyer:* {deal['buyer']}\n"
        f"*Deal Info:* {deal['info']}\n"
        f"*Amount:* {deal['amount']} USDT\n"
        f"*Time to Complete:* {deal['time']} hours\n\n"
        f"*Fees:* {fee_text}\n"
        f"*Status:* Ongoing"
    )

# Start polling
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from config import TOKEN, LOGS_CHAT_ID, ADMINS, ESCROW_FEE_PERCENT

bot = Bot(token=TOKEN, parse_mode=ParseMode.MARKDOWN_V2)
dp = Dispatcher()

deals = {}
fees_selected = {}

def escape_md_v2(text):
    special_chars = "_*[]()~`>#+-=|{}.!\\"
    return ''.join(f'\\{char}' if char in special_chars else char for char in text)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.reply("Welcome to the Escrow Bot\\!\nUse /create to begin a new deal\\.")

@dp.message(Command("create"))
async def create_command(message: types.Message):
    await message.reply(
        "Please fill the deal form in the following format:\n\n"
        "Seller : @username\n"
        "Buyer : @username\n"
        "Deal Info : (brief description)\n"
        "Amount (In USDT) : (amount)\n"
        "Time To Complete : (time in hours)"
    )

@dp.message()
async def form_handler(message: types.Message):
    if not message.text.startswith("Seller :") or "Buyer :" not in message.text:
        return

    lines = message.text.split('\n')
    if len(lines) < 5:
        await message.reply("Invalid format. Please follow the correct format.")
        return

    try:
        seller = lines[0].split(':')[1].strip()
        buyer = lines[1].split(':')[1].strip()
        deal_info = lines[2].split(':')[1].strip()
        amount = float(lines[3].split(':')[1].strip())
        time = lines[4].split(':')[1].strip()
    except Exception as e:
        await message.reply(f"Error reading form: {e}")
        return

    deal_id = f"DEAL-{message.chat.id}-{message.message_id}"
    deals[deal_id] = {
        'seller': seller,
        'buyer': buyer,
        'amount': amount,
        'time': time,
        'deal_info': deal_info,
        'confirmed': {seller: False, buyer: False}
    }

    form_text = (
        f"✅ *Form received\\!*\n"
        f"*Seller:* {escape_md_v2(seller)}\n"
        f"*Buyer:* {escape_md_v2(buyer)}\n"
        f"*Deal Info:* {escape_md_v2(deal_info)}\n"
        f"*Amount \\(In USDT\\):* {amount}\n"
        f"*Time To Complete:* {escape_md_v2(time)} hours\n\n"
        "Both of you confirm your roles:"
    )

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{seller} (Seller)", callback_data=f"confirm_{deal_id}_seller")],
        [InlineKeyboardButton(text=f"{buyer} (Buyer)", callback_data=f"confirm_{deal_id}_buyer")]
    ])

    sent_message = await message.reply(form_text, reply_markup=buttons)

    deals[deal_id]['message_id'] = sent_message.message_id

    # Forward to log group
    log_text = f"New Deal Created \\- ID: `{deal_id}`\n\n{form_text}"
    await bot.send_message(LOGS_CHAT_ID, log_text, parse_mode=ParseMode.MARKDOWN_V2)

@dp.callback_query()
async def confirmation_handler(call: types.CallbackQuery):
    data = call.data.split('_')
    if len(data) != 3:
        return

    action, deal_id, role = data
    if deal_id not in deals:
        await call.answer("This deal no longer exists.")
        return

    deal = deals[deal_id]
    user = call.from_user.username
    expected_user = deal['seller'] if role == 'seller' else deal['buyer']

    if f"@{user}" != expected_user:
        await call.answer("You are not authorized for this role.")
        return

    deals[deal_id]['confirmed'][expected_user] = True
    await call.message.edit_reply_markup(reply_markup=None)

    # Check if both confirmed
    if all(deal['confirmed'].values()):
        await handle_fees_selection(call.message, deal_id)
    else:
        await call.message.answer(f"{expected_user} has confirmed their role. Waiting for the other party.")

async def handle_fees_selection(message: types.Message, deal_id: str):
    deal = deals[deal_id]
    seller = deal['seller']
    buyer = deal['buyer']

    text = "Who will pay the 2% escrow fee?"
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{seller} - I Pay Full", callback_data=f"fees_{deal_id}_seller")],
        [InlineKeyboardButton(text=f"{buyer} - I Pay Full", callback_data=f"fees_{deal_id}_buyer")],
        [InlineKeyboardButton(text="Split 50/50", callback_data=f"fees_{deal_id}_split")]
    ])
    await message.answer(text, reply_markup=buttons)

@dp.callback_query()
async def fees_handler(call: types.CallbackQuery):
    data = call.data.split('_')
    if len(data) != 3:
        return

    action, deal_id, option = data
    if deal_id not in deals or deal_id in fees_selected:
        await call.answer("Fees already chosen.")
        return

    deal = deals[deal_id]
    user = call.from_user.username
    user_role = 'seller' if f"@{user}" == deal['seller'] else 'buyer' if f"@{user}" == deal['buyer'] else None

    if not user_role:
        await call.answer("This is not your deal.")
        return

    fees_selected[deal_id] = option
    fee_message = ""

    if option == "split":
        fee_message = "Both of you will split the 2% fees."
    else:
        fee_message = f"{user_role.capitalize()} pays the full 2% fees."

    await call.message.edit_text(fee_message)

    # Update pinned message to "Ongoing Deal"
    chat_id = call.message.chat.id
    form_text = (
        f"✅ *Ongoing Deal*\n"
        f"*Deal ID:* `{deal_id}`\n"
        f"*Seller:* {escape_md_v2(deal['seller'])}\n"
        f"*Buyer:* {escape_md_v2(deal['buyer'])}\n"
        f"*Deal Info:* {escape_md_v2(deal['deal_info'])}\n"
        f"*Amount \\(In USDT\\):* {deal['amount']}\n"
        f"*Time To Complete:* {escape_md_v2(deal['time'])} hours\n\n"
        f"*Fees:* {fee_message}\n"
    )
    await bot.edit_message_text(form_text, chat_id, deal['message_id'], parse_mode=ParseMode.MARKDOWN_V2)
    await bot.pin_chat_message(chat_id, deal['message_id'])

    await bot.send_message(LOGS_CHAT_ID, f"✅ Deal Confirmed & Ongoing: `{deal_id}`", parse_mode=ParseMode.MARKDOWN_V2)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

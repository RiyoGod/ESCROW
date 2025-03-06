import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import TOKEN, LOGS_CHAT_ID, ADMINS

dp = Dispatcher()
bot = Bot(token=TOKEN, parse_mode=ParseMode.MARKDOWN_V2)

# Deal Storage
ongoing_deals = {}

# Escape function for MarkdownV2
def escape_md_v2(text: str) -> str:
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

# Command /create
@dp.message(Command("create"))
async def create_command(message: types.Message):
    if message.chat.type != 'group':
        await message.reply("This command only works inside a group.")
        return

    await message.reply(
        escape_md_v2(
            "Fill the form in this format:\n\n"
            "Seller : @username\n"
            "Buyer : @username\n"
            "Deal Info : [Short description]\n"
            "Amount (In USDT) : [Amount]\n"
            "Time To Complete : [Hours]\n\n"
            "After filling, send it here."
        )
    )

# Form detection
@dp.message()
async def handle_form(message: types.Message):
    if not message.text.startswith("Seller :"):
        return

    lines = message.text.split("\n")
    if len(lines) < 5:
        await message.reply("Invalid format. Please check and resend.")
        return

    seller = lines[0].split(":")[1].strip()
    buyer = lines[1].split(":")[1].strip()
    deal_info = lines[2].split(":")[1].strip()
    amount = lines[3].split(":")[1].strip()
    time = lines[4].split(":")[1].strip()

    chat_id = message.chat.id
    deal_id = f"{chat_id}_{message.message_id}"

    ongoing_deals[deal_id] = {
        "seller": seller,
        "buyer": buyer,
        "deal_info": deal_info,
        "amount": amount,
        "time": time,
        "confirmed": {"seller": False, "buyer": False},
        "fees_chosen": False,
        "fees_payer": None,
        "message_id": message.message_id,
    }

    form_text = (
        "✅ Form received!\n\n"
        f"Seller : {escape_md_v2(seller)}\n"
        f"Buyer : {escape_md_v2(buyer)}\n"
        f"Deal Info : {escape_md_v2(deal_info)}\n"
        f"Amount \\(In USDT\\) : {escape_md_v2(amount)}\n"
        f"Time To Complete : {escape_md_v2(time)}\n\n"
        "Both of you confirm your roles below:"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text=f"{seller} - Confirm", callback_data=f"confirm_seller_{deal_id}")
    builder.button(text=f"{buyer} - Confirm", callback_data=f"confirm_buyer_{deal_id}")

    await message.reply(form_text, reply_markup=builder.as_markup(), parse_mode=ParseMode.MARKDOWN_V2)

    log_text = (
        "New Deal Created!\n\n"
        f"Seller : {escape_md_v2(seller)}\n"
        f"Buyer : {escape_md_v2(buyer)}\n"
        f"Deal Info : {escape_md_v2(deal_info)}\n"
        f"Amount \\(In USDT\\) : {escape_md_v2(amount)}\n"
        f"Time To Complete : {escape_md_v2(time)}"
    )
    await bot.send_message(LOGS_CHAT_ID, log_text, parse_mode=ParseMode.MARKDOWN_V2)

# Confirmation Handler
@dp.callback_query()
async def handle_confirmation(callback: types.CallbackQuery):
    data = callback.data
    if not data.startswith("confirm_") and not data.startswith("fees_"):
        return

    parts = data.split("_")
    action = parts[0]
    role = parts[1]
    deal_id = "_".join(parts[2:])

    if deal_id not in ongoing_deals:
        await callback.answer("This deal does not exist.")
        return

    deal = ongoing_deals[deal_id]
    username = f"@{callback.from_user.username}"

    if role == "seller" and username != deal["seller"]:
        await callback.answer("You are not the seller.")
        return
    if role == "buyer" and username != deal["buyer"]:
        await callback.answer("You are not the buyer.")
        return

    if action == "confirm":
        deal["confirmed"][role] = True
        await callback.answer(f"{role.capitalize()} confirmed!")

        if deal["confirmed"]["seller"] and deal["confirmed"]["buyer"]:
            builder = InlineKeyboardBuilder()
            builder.button(text="Split Fees", callback_data=f"fees_split_{deal_id}")
            builder.button(text="I'll Pay All", callback_data=f"fees_mine_{deal_id}")
            await callback.message.edit_text(
                escape_md_v2("✅ Both confirmed! Who will pay the fees?"),
                reply_markup=builder.as_markup(),
                parse_mode=ParseMode.MARKDOWN_V2
            )
    elif action == "fees":
        if deal["fees_chosen"]:
            await callback.answer("Fees already chosen.")
            return

        deal["fees_chosen"] = True
        if parts[2] == "split":
            deal["fees_payer"] = "split"
            await callback.message.edit_text(
                escape_md_v2("✅ Fees will be split between both."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            deal["fees_payer"] = username
            await callback.message.edit_text(
                escape_md_v2(f"✅ {username} will pay all the fees."),
                parse_mode=ParseMode.MARKDOWN_V2
            )

        await finalize_deal(callback.message.chat.id, callback.message.message_id, deal)

async def finalize_deal(chat_id, message_id, deal):
    pinned_message = (
        "📌 Ongoing Deal\n\n"
        f"Seller : {escape_md_v2(deal['seller'])}\n"
        f"Buyer : {escape_md_v2(deal['buyer'])}\n"
        f"Deal Info : {escape_md_v2(deal['deal_info'])}\n"
        f"Amount \\(In USDT\\) : {escape_md_v2(deal['amount'])}\n"
        f"Time To Complete : {escape_md_v2(deal['time'])}\n\n"
        f"Fees Paid By: {escape_md_v2(deal['fees_payer']) if deal['fees_payer'] != 'split' else 'Both (Split)'}"
    )

    sent = await bot.send_message(chat_id, pinned_message, parse_mode=ParseMode.MARKDOWN_V2)
    await bot.pin_chat_message(chat_id, sent.message_id)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    

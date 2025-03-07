import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import config
import random

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.TOKEN, parse_mode="HTML")
dp = Dispatcher()

deals = {}

def generate_escrow_id():
    return f"ESCROW-{random.randint(100000, 999999)}"

def confirm_buttons(deal_id, role):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Seller Confirmed" if role == "seller" else "✅ Seller Confirm", 
                              callback_data=f"confirm:seller:{deal_id}")],
        [InlineKeyboardButton(text="✅ Buyer Confirmed" if role == "buyer" else "✅ Buyer Confirm", 
                              callback_data=f"confirm:buyer:{deal_id}")]
    ])

def fees_buttons(deal_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Mine (Seller Pays Full)", callback_data=f"fees:mine:{deal_id}")],
        [InlineKeyboardButton(text="Split (Both Pay 50/50)", callback_data=f"fees:split:{deal_id}")]
    ])

@dp.message(Command("create"))
async def create_command(message: Message):
    if message.chat.type != "supergroup" and message.chat.type != "group":
        await message.reply("This command only works in groups.")
        return

    await message.reply(
        "Fill this form in reply to this message:\n\n"
        "Seller: @username\n"
        "Buyer: @username\n"
        "Deal Info: description\n"
        "Amount (In USDT): amount\n"
        "Time To Complete: hours"
    )

@dp.message(F.reply_to_message, F.text.regexp(r"Seller: @(\w+)\nBuyer: @(\w+)\nDeal Info: (.+)\nAmount In USDT: (\d+)\nTime To Complete: (\d+)"))
async def process_deal_form(message: Message):
    form = message.text.strip().split("\n")
    seller = form[0].split("@")[1]
    buyer = form[1].split("@")[1]
    deal_info = form[2].split(": ")[1]
    amount = form[3].split(": ")[1]
    time = form[4].split(": ")[1]

    deal_id = generate_escrow_id()

    deals[deal_id] = {
        "seller": f"@{seller}",
        "buyer": f"@{buyer}",
        "deal_info": deal_info,
        "amount": amount,
        "time": time,
        "confirmed": {"seller": False, "buyer": False},
        "fees_chosen": False
    }

    await message.reply(
        f"✅ Form received!\n\n"
        f"Seller: @{seller}\n"
        f"Buyer: @{buyer}\n"
        f"Deal Info: {deal_info}\n"
        f"Amount (In USDT): {amount}\n"
        f"Time To Complete: {time}\n\n"
        "Both of you confirm your roles:",
        reply_markup=confirm_buttons(deal_id, None)
    )

@dp.callback_query(F.data.startswith("confirm:"))
async def confirm_callback(callback: types.CallbackQuery):
    _, role, deal_id = callback.data.split(":")
    user = callback.from_user.username

    deal = deals.get(deal_id)
    if not deal:
        await callback.answer("Deal not found!")
        return

    if (role == "seller" and user != deal['seller'][1:]) or (role == "buyer" and user != deal['buyer'][1:]):
        await callback.answer(f"Only {role.capitalize()} can confirm.")
        return

    if deal["confirmed"][role]:
        await callback.answer(f"{role.capitalize()} already confirmed.")
        return

    deal["confirmed"][role] = True

    await bot.send_message(
        callback.message.chat.id,
        f"{deal[role]} confirmed the deal. Waiting for {deal['buyer' if role == 'seller' else 'seller']}."
    )

    if deal["confirmed"]["seller"] and deal["confirmed"]["buyer"]:
        await bot.send_message(
            callback.message.chat.id,
            f"✅ Both confirmed!\n\nWho will pay the fees?",
            reply_markup=fees_buttons(deal_id)
        )

    await callback.message.edit_reply_markup(reply_markup=confirm_buttons(deal_id, role))

@dp.callback_query(F.data.startswith("fees:"))
async def fees_callback(callback: types.CallbackQuery):
    _, choice, deal_id = callback.data.split(":")
    deal = deals.get(deal_id)
    if not deal:
        await callback.answer("Deal not found!")
        return

    if deal["fees_chosen"]:
        await callback.answer("Fees already chosen.")
        return

    deal["fees_chosen"] = True

    if choice == "mine":
        payer = "Seller"
        msg = f"{deal['seller']} chose to pay full fees."
    else:
        payer = "Split"
        msg = "Split chosen, both will pay fees equally."

    await bot.send_message(callback.message.chat.id, msg)

    pinned_msg = await bot.send_message(
        callback.message.chat.id,
        f"✅ Ongoing Deal - {deal_id}\n\n"
        f"Seller: {deal['seller']}\n"
        f"Buyer: {deal['buyer']}\n"
        f"Deal Info: {deal['deal_info']}\n"
        f"Amount (In USDT): {deal['amount']}\n"
        f"Time To Complete: {deal['time']}\n"
        f"Fees Mode: {payer}",
    )

    await bot.pin_chat_message(callback.message.chat.id, pinned_msg.message_id)

    await callback.message.edit_reply_markup(reply_markup=None)

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)

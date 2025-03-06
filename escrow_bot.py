import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from config import TOKEN, LOGS_CHAT_ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

deals = {}  # {deal_id: {creator, seller, buyer, info, amount, time, fee, confirmed_seller, confirmed_buyer}}

def calculate_fee(amount):
    try:
        amount = float(amount)
        fee = amount * 0.02  # 2% escrow fee
        return round(fee, 2)
    except ValueError:
        return "Invalid Amount"

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.reply("Welcome to AutoEscrow Bot! Use /create to start a deal.")

@dp.message(Command("create"))
async def create(message: types.Message):
    deal_form = (
        "Fill this form to start the deal:\n\n"
        "Seller :\n"
        "Buyer :\n"
        "Deal Info :\n"
        "Amount (In USDT) :\n"
        "Time To Complete : (in minutes)\n\n"
        "Reply to this message with the filled form."
    )
    await message.reply(deal_form)

@dp.message()
async def handle_form_reply(message: types.Message):
    if message.reply_to_message and "Fill this form to start the deal:" in message.reply_to_message.text:
        lines = message.text.strip().split("\n")
        if len(lines) < 5:
            await message.reply("Invalid format. Please fill all fields correctly.")
            return

        seller = lines[0].replace("Seller :", "").strip()
        buyer = lines[1].replace("Buyer :", "").strip()
        deal_info = lines[2].replace("Deal Info :", "").strip()
        amount = lines[3].replace("Amount (In USDT) :", "").strip()
        time_to_complete = lines[4].replace("Time To Complete :", "").strip()

        fee = calculate_fee(amount)

        deal_id = message.message_id
        deals[deal_id] = {
            "creator": message.from_user.username,
            "seller": seller,
            "buyer": buyer,
            "info": deal_info,
            "amount": amount,
            "time": time_to_complete,
            "fee": fee,
            "confirmed_seller": False,
            "confirmed_buyer": False,
        }

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"I am Seller ({seller})", callback_data=f"confirm_seller_{deal_id}")],
                [InlineKeyboardButton(text=f"I am Buyer ({buyer})", callback_data=f"confirm_buyer_{deal_id}")]
            ]
        )

        text = (
            f"**New Deal Created!**\n\n"
            f"**Deal ID:** {deal_id}\n"
            f"**Created By:** @{message.from_user.username}\n"
            f"**Seller:** {seller}\n"
            f"**Buyer:** {buyer}\n"
            f"**Deal Info:** {deal_info}\n"
            f"**Amount:** {amount} USDT\n"
            f"**Escrow Fee (2%):** {fee} USDT\n"
            f"**Time To Complete:** {time_to_complete} Minutes"
        )

        await bot.send_message(LOGS_CHAT_ID, text, reply_markup=keyboard, parse_mode="Markdown")

async def update_confirmation_message(deal_id):
    deal = deals.get(deal_id)
    if not deal:
        return

    text = (
        f"**Deal ID:** {deal_id}\n"
        f"**Created By:** @{deal['creator']}\n"
        f"**Seller:** {deal['seller']} {'✅' if deal['confirmed_seller'] else '❌'}\n"
        f"**Buyer:** {deal['buyer']} {'✅' if deal['confirmed_buyer'] else '❌'}\n"
        f"**Deal Info:** {deal['info']}\n"
        f"**Amount:** {deal['amount']} USDT\n"
        f"**Escrow Fee (2%):** {deal['fee']} USDT\n"
        f"**Time To Complete:** {deal['time']} Minutes"
    )

    keyboard = []
    if not deal['confirmed_seller']:
        keyboard.append([InlineKeyboardButton(text=f"I am Seller ({deal['seller']})", callback_data=f"confirm_seller_{deal_id}")])
    if not deal['confirmed_buyer']:
        keyboard.append([InlineKeyboardButton(text=f"I am Buyer ({deal['buyer']})", callback_data=f"confirm_buyer_{deal_id}")])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None

    await bot.send_message(LOGS_CHAT_ID, text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data.startswith("confirm_seller_") or c.data.startswith("confirm_buyer_"))
async def confirm(callback: types.CallbackQuery):
    deal_id = int(callback.data.split("_")[-1])

    if deal_id not in deals:
        await callback.answer("Deal not found!")
        return

    deal = deals[deal_id]
    user = callback.from_user.username
    role = "seller" if "seller" in callback.data else "buyer"

    expected_user = deal[role].replace("@", "").strip()
    if user != expected_user:
        await callback.answer(f"Only the {role} can confirm this deal.")
        return

    deals[deal_id][f"confirmed_{role}"] = True
    await callback.answer(f"{role.capitalize()} confirmed!")

    if deals[deal_id]["confirmed_seller"] and deals[deal_id]["confirmed_buyer"]:
        final_text = (
            f"**Deal ID {deal_id} is now fully confirmed by both parties!**\n\n"
            f"**Created By:** @{deal['creator']}\n"
            f"**Seller:** {deal['seller']} ✅\n"
            f"**Buyer:** {deal['buyer']} ✅\n"
            f"**Deal Info:** {deal['info']}\n"
            f"**Amount:** {deal['amount']} USDT\n"
            f"**Escrow Fee (2%):** {deal['fee']} USDT\n"
            f"**Time To Complete:** {deal['time']} Minutes\n\n"
            "This deal is now locked and both parties have agreed."
        )
        await bot.send_message(LOGS_CHAT_ID, final_text, parse_mode="Markdown")
    else:
        await update_confirmation_message(deal_id)

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))

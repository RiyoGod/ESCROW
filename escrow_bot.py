import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.utils import markdown
import asyncio
import datetime
from config import TOKEN, LOG_GROUP_ID, ADMINS

bot = Bot(token=TOKEN)
dp = Dispatcher()

ongoing_deals = {}

def generate_deal_id():
    return str(int(datetime.datetime.now().timestamp()))

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Welcome to AutoEscrow Bot! Use /create to start a new deal.")

@dp.message(Command("create"))
async def create_deal(message: types.Message):
    deal_id = generate_deal_id()
    ongoing_deals[deal_id] = {"creator": message.from_user.id}

    await message.answer(f"Fill this form to start the deal:\n\n"
                         f"Seller :\n"
                         f"Buyer :\n"
                         f"Deal Info :\n"
                         f"Amount (In USDT) :\n"
                         f"Time To Complete : (in minutes)\n\n"
                         f"Reply to this message with the filled form.")

@dp.message()
async def handle_deal_form(message: types.Message):
    if message.reply_to_message and message.reply_to_message.text.startswith("Fill this form"):
        lines = message.text.split("\n")
        if len(lines) < 5:
            await message.reply("Invalid format! Please fill all fields.")
            return

        seller = lines[0].split(":")[1].strip()
        buyer = lines[1].split(":")[1].strip()

        deal_id = generate_deal_id()
        ongoing_deals[deal_id] = {
            'form': message.text,
            'confirmed': set(),
            'seller': seller,
            'buyer': buyer
        }

        confirm_buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(f"Confirm: {seller} (Seller)", callback_data=f'confirm_{deal_id}_seller')],
            [InlineKeyboardButton(f"Confirm: {buyer} (Buyer)", callback_data=f'confirm_{deal_id}_buyer')]
        ])

        deal_msg = (f"New Deal Created!\n\n"
                    f"**Deal ID:** `{deal_id}`\n\n"
                    f"{markdown.pre(message.text)}")

        await message.answer(deal_msg, parse_mode=ParseMode.MARKDOWN, reply_markup=confirm_buttons)

        await bot.send_message(LOG_GROUP_ID, f"New Deal Created:\n\n{message.text}\nDeal ID: {deal_id}")

@dp.callback_query()
async def handle_callbacks(query: types.CallbackQuery):
    data = query.data.split("_")
    action, deal_id, role = data[0], data[1], data[2]

    if deal_id not in ongoing_deals:
        await query.answer("This deal does not exist or expired.")
        return

    deal = ongoing_deals[deal_id]
    username = f"@{query.from_user.username}"

    if action == "confirm":
        expected_user = deal[role]
        if username != expected_user:
            await query.answer(f"Only {expected_user} can confirm as {role.capitalize()}.")
            return

        deal['confirmed'].add(role)

        await query.message.answer(f"{username} confirmed as {role.capitalize()} for Deal ID `{deal_id}`", parse_mode=ParseMode.MARKDOWN)

        if len(deal['confirmed']) == 2:
            fee_buttons = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Split Fees", callback_data=f'fees_{deal_id}_split')],
                [InlineKeyboardButton("I will Pay Fees", callback_data=f'fees_{deal_id}_single')]
            ])
            await query.message.answer(f"Both parties confirmed! Who will pay the 2% fees for Deal ID `{deal_id}`?", reply_markup=fee_buttons, parse_mode=ParseMode.MARKDOWN)

            # Pin the deal in group
            pinned_msg = await query.message.answer(f"On Going Deal - Deal ID: {deal_id}\n\n{markdown.pre(deal['form'])}", parse_mode=ParseMode.MARKDOWN)
            await bot.pin_chat_message(query.message.chat.id, pinned_msg.message_id)

            await bot.send_message(LOG_GROUP_ID, f"Deal Confirmed & Started - Deal ID: {deal_id}\n\n{deal['form']}", parse_mode=ParseMode.MARKDOWN)

    elif action == "fees":
        choice = role

        await bot.delete_message(query.message.chat.id, query.message.message_id)

        fee_text = "✅ Fees will be split equally between both parties." if choice == "split" else "✅ One party will cover all fees."
        await query.message.answer(f"Deal ID `{deal_id}`: {fee_text}", parse_mode=ParseMode.MARKDOWN)

        await bot.send_message(LOG_GROUP_ID, f"Fee Decision for Deal ID `{deal_id}`: {fee_text}", parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("dispute"))
async def handle_dispute(message: types.Message):
    await message.answer("Dispute raised! Admins will join to assist.")
    dispute_msg = f"⚠️ Dispute Alert!\n\nRaised by: @{message.from_user.username}\n\nPlease join the group to resolve the dispute."
    for admin_id in ADMINS:
        await bot.send_message(admin_id, dispute_msg)
    await bot.send_message(LOG_GROUP_ID, dispute_msg)

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

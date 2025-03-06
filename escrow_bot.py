import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from aiogram.utils import executor
from datetime import datetime
from config import TOKEN, LOG_GROUP_ID, ADMINS

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

ongoing_deals = {}  # To store deal data (temporary memory)

# Start Command
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.reply("Welcome to Crypto Escrow Bot! Use /create to start a new deal.")

# Create Deal Flow
@dp.message_handler(commands=['create'])
async def create_deal(message: types.Message):
    deal_form = ("Please fill the deal form in this format:\n\n"
                 "Seller: @username\n"
                 "Buyer: @username\n"
                 "Deal Info: Short description\n"
                 "Amount (In USDT): Amount\n"
                 "Time To Complete: e.g., 24 hours")

    await message.reply(deal_form)

@dp.message_handler(lambda message: "Seller:" in message.text and "Buyer:" in message.text)
async def handle_deal_form(message: types.Message):
    deal_id = str(int(datetime.now().timestamp()))
    ongoing_deals[deal_id] = {'form': message.text, 'confirmed': set(), 'creator': message.from_user.id}

    deal_text = f"**New Deal Created!**\n\n{message.text}\n\nDeal ID: `{deal_id}`"
    confirm_buttons = InlineKeyboardMarkup()
    confirm_buttons.add(
        InlineKeyboardButton("I am Seller", callback_data=f'confirm_{deal_id}_seller'),
        InlineKeyboardButton("I am Buyer", callback_data=f'confirm_{deal_id}_buyer')
    )

    await message.reply(deal_text, reply_markup=confirm_buttons, parse_mode=ParseMode.MARKDOWN)

    # Forward to log group
    await bot.send_message(LOG_GROUP_ID, f"New Deal Created:\n\n{message.text}\n\nDeal ID: {deal_id}")

# Confirmations (Seller/Buyer)
@dp.callback_query_handler(lambda c: c.data.startswith('confirm_'))
async def confirm_deal(callback_query: types.CallbackQuery):
    _, deal_id, role = callback_query.data.split('_')
    user = callback_query.from_user.username

    if deal_id not in ongoing_deals:
        await callback_query.answer("Deal not found or expired.")
        return

    ongoing_deals[deal_id]['confirmed'].add(role)

    # Edit the original message to show who confirmed
    confirmation_text = f"@{user} confirmed as {role.capitalize()} for Deal ID `{deal_id}`"
    await bot.send_message(callback_query.message.chat.id, confirmation_text, parse_mode=ParseMode.MARKDOWN)

    if len(ongoing_deals[deal_id]['confirmed']) == 2:
        # Both confirmed - Start fee selection
        fee_buttons = InlineKeyboardMarkup()
        fee_buttons.add(
            InlineKeyboardButton("Split Fees", callback_data=f'fees_{deal_id}_split'),
            InlineKeyboardButton("I will Pay Fees", callback_data=f'fees_{deal_id}_single')
        )

        await bot.send_message(callback_query.message.chat.id, 
            f"Both parties confirmed! Who will pay the 2% fees for Deal ID `{deal_id}`?",
            reply_markup=fee_buttons, parse_mode=ParseMode.MARKDOWN
        )
        # Pin message
        deal_message = await bot.send_message(callback_query.message.chat.id, 
            f"**On Going Deal - Deal ID: `{deal_id}`**\n\n{ongoing_deals[deal_id]['form']}", 
            parse_mode=ParseMode.MARKDOWN)
        await bot.pin_chat_message(callback_query.message.chat.id, deal_message.message_id)

# Fee Split / Payment Choice
@dp.callback_query_handler(lambda c: c.data.startswith('fees_'))
async def handle_fees(callback_query: types.CallbackQuery):
    _, deal_id, choice = callback_query.data.split('_')

    if deal_id not in ongoing_deals:
        await callback_query.answer("Deal not found or expired.")
        return

    fee_text = "✅ Fees will be split equally between both parties." if choice == "split" else "✅ One party will cover all fees."
    await bot.send_message(callback_query.message.chat.id, 
                           f"Deal ID `{deal_id}`: {fee_text}", 
                           parse_mode=ParseMode.MARKDOWN)

    # Notify log group too
    await bot.send_message(LOG_GROUP_ID, 
        f"Deal `{deal_id}` fees decision:\n{fee_text}", parse_mode=ParseMode.MARKDOWN)

# Check Balance Command (Placeholder for future crypto handling)
@dp.message_handler(commands=['balance'])
async def balance_command(message: types.Message):
    await message.reply("Balance checking will be added after payment handling is integrated.")

# Dispute Command
@dp.message_handler(commands=['dispute'])
async def dispute_command(message: types.Message):
    dispute_text = (f"🚨 Dispute Raised!\nUser: @{message.from_user.username}\n"
                    f"Please check log group to resolve this.\n\n"
                    f"Log Group: [Join Here](https://t.me/YOUR_LOG_GROUP_LINK)")
    await message.reply(dispute_text, parse_mode=ParseMode.MARKDOWN)

    # Alert Admins in log group
    await bot.send_message(LOG_GROUP_ID, 
        f"🚨 Dispute Alert! User @{message.from_user.username} raised a dispute.\n\nPlease review the chat ASAP.",
        parse_mode=ParseMode.MARKDOWN)

# Terms and Instructions
@dp.message_handler(commands=['terms'])
async def terms_command(message: types.Message):
    await message.reply("📜 Terms of Service:\n1. Both parties must confirm deal.\n2. 2% escrow fee applies.\n3. Payments handled via crypto.\n4. Admin decision in dispute is final.")

@dp.message_handler(commands=['instructions'])
async def instructions_command(message: types.Message):
    await message.reply("ℹ️ Instructions:\n1. Use /create to start.\n2. Fill form correctly.\n3. Both confirm deal.\n4. Choose fee option.\n5. Funds move into escrow.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

from aiogram import types, Dispatcher
from utils.logger import log_new_deal
from config import LOG_GROUP_ID
from utils.time_helper import current_utc_time

ongoing_deals = {}

async def create_cmd(message: types.Message):
    await message.reply("Fill this form:\n\n"
                        "Seller: @SellerUsername\n"
                        "Buyer: @BuyerUsername\n"
                        "Deal Info: Describe the deal\n"
                        "Amount (in USDT): 50\n"
                        "Time To Complete: 24 hours")

    ongoing_deals[message.chat.id] = {"creator": message.from_user.id}

async def deal_form(message: types.Message):
    if message.chat.id not in ongoing_deals:
        return

    data = message.text.split("\n")
    if len(data) < 5:
        return await message.reply("Invalid format. Please fill all fields correctly.")

    deal_id = f"#ESC{int(message.date.timestamp())}"

    deal = {
        "id": deal_id,
        "seller": data[0].split(":")[1].strip(),
        "buyer": data[1].split(":")[1].strip(),
        "info": data[2].split(":")[1].strip(),
        "amount": data[3].split(":")[1].strip(),
        "duration": data[4].split(":")[1].strip(),
        "created_at": current_utc_time(),
        "message_id": message.message_id + 1
    }

    ongoing_deals[message.chat.id].update(deal)

    confirm_msg = await message.reply(
        f"✅ Deal Created!\n\n"
        f"Deal ID: {deal_id}\n"
        f"Seller: {deal['seller']}\n"
        f"Buyer: {deal['buyer']}\n"
        f"Deal Info: {deal['info']}\n"
        f"Amount: {deal['amount']} USDT\n"
        f"Time to Complete: {deal['duration']}\n\n"
        f"@{deal['seller']} & @{deal['buyer']} Please Confirm via buttons below!"
    )

    await log_new_deal(message.bot, deal)

    await message.bot.pin_chat_message(message.chat.id, confirm_msg.message_id)
    await message.bot.edit_message_text(
        "📌 ONGOING DEAL\n\n" + confirm_msg.text,
        message.chat.id,
        confirm_msg.message_id
    )

def register(dp: Dispatcher):
    dp.register_message_handler(create_cmd, commands=["create"])
    dp.register_message_handler(deal_form)


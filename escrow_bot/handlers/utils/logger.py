from config import LOG_GROUP_ID, ADMINS
from utils.time_helper import current_utc_time

async def log_new_deal(bot, deal):
    text = (
        f"📑 [NEW DEAL CREATED]\n\n"
        f"Deal ID: {deal['id']}\n"
        f"Seller: {deal['seller']}\n"
        f"Buyer: {deal['buyer']}\n"
        f"Deal Info: {deal['info']}\n"
        f"Amount: {deal['amount']} USDT\n"
        f"Time To Complete: {deal['duration']}\n"
        f"Created At: {deal['created_at']}"
    )
    await bot.send_message(LOG_GROUP_ID, text)

async def log_dispute(bot, deal_id, chat_id):
    chat_link = f"https://t.me/c/{str(chat_id).replace('-100', '')}"  # Private group link format
    text = (
        f"⚠️ [DISPUTE ALERT]\n\n"
        f"Deal ID: {deal_id}\n"
        f"Dispute Raised At: {current_utc_time()}\n\n"
        f"Join Chat: [Open Chat]({chat_link})"
    )
    await bot.send_message(LOG_GROUP_ID, text, disable_web_page_preview=True)

    for admin in ADMINS:
        await bot.send_message(LOG_GROUP_ID, f"👮‍♂️ Admin Alert: <a href='tg://user?id={admin}'>Admin</a>", parse_mode="HTML")
      

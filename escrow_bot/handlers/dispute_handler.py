from aiogram import types, Dispatcher
from utils.logger import log_dispute

async def dispute_cmd(message: types.Message):
    await log_dispute(message.bot, "Unknown (for now)", message.chat.id)
    await message.reply("⚠️ Dispute reported! Admins will join to assist.")

def register(dp: Dispatcher):
    dp.register_message_handler(dispute_cmd, commands=["dispute"])
  

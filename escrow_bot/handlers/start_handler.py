from aiogram import types, Dispatcher

async def start_cmd(message: types.Message):
    await message.reply("Welcome to the Escrow Bot! Use /create to start a new deal.")

def register(dp: Dispatcher):
    dp.register_message_handler(start_cmd, commands=["start", "menu"])
  

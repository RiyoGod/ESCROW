from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import TOKEN
from handlers import start_handler, deal_handler, dispute_handler

bot = Bot(token=TOKEN, parse_mode='HTML')
dp = Dispatcher(bot)

# Register Handlers
start_handler.register(dp)
deal_handler.register(dp)
dispute_handler.register(dp)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

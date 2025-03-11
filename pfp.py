import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message

TOKEN = "8057286738:AAHlmI-nOSqTjamN6k_PGURzniuLc-7lerM"

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Random Emoji Selection
async def animate_emoji(message: Message):
    emojis = ["❤️", "🔥", "🎉"]
    chosen_emoji = random.choice(emojis)
    
    # Creating a smooth effect by sending one character at a time
    animated_text = ""
    for char in chosen_emoji * 5:  # Repeat emoji for effect
        animated_text += char
        await message.edit_text(animated_text)
        await asyncio.sleep(0.2)  # Smooth transition

# Start Command
@dp.message(CommandStart())
async def start_command(message: Message):
    start_text = f"""
<b>Hey  — <i>RIO</i>, 💗</b>

⊛ <b>THIS IS NEXIUS MUSIC!</b>

➜ <b>NEXIUS MUSIC</b> is your personal music companion, here to bring harmony to your day. Enjoy seamless music playback, curated playlists, and effortless control, all at your fingertips.

<b>Supported Platforms:</b> YouTube, Spotify, Resso, Apple Music, and SoundCloud.

⊛ Click on the help button to get information about my modules and commands.
"""
    
    sent_message = await message.answer(start_text)
    await asyncio.sleep(1)
    
    # Call the emoji animation function
    await animate_emoji(sent_message)

# Run the bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

import aiohttp
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile
from aiogram.filters import Command
from io import BytesIO

# BOT CONFIGURATION
TOKEN = "7782987492:AAGOIiMokMR1tfkCgGbmufjUvwmJvF2MyjY"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# IMAGE SOURCES
ANIME_SOURCES = [
    "https://api.jikan.moe/v4/anime?q={query}",  # MyAnimeList API
    "https://api.anilist.co/graphql",           # AniList API (GraphQL)
    "https://www.zerochan.net/{query}?s=4",     # Zerochan 4K images
    "https://danbooru.donmai.us/posts.json?tags={query}&limit=5",  # Danbooru (NSFW filter optional)
    "https://wall.alphacoders.com/search.php?search={query}"  # Wallpaper Abyss
]

# LOGGING
logging.basicConfig(level=logging.INFO)

async def fetch_images(query):
    """Fetch high-quality images from different anime sources."""
    headers = {"User-Agent": "YorX PFP Bot"}
    
    for url in ANIME_SOURCES:
        search_url = url.format(query=query.replace(" ", "+"))
        
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        images = extract_images(data)
                        if images:
                            return images  # Return first valid set of images

    return None  # No images found

def extract_images(data):
    """Extracts images from API response."""
    images = []
    if "data" in data:  # For Jikan (MyAnimeList) API
        for anime in data["data"]:
            if "images" in anime:
                images.append(anime["images"]["jpg"]["large_image_url"])
    elif isinstance(data, list):  # For Danbooru API
        for post in data:
            if "file_url" in post:
                images.append(post["file_url"])
    return images[:5]  # Return top 5 images

@dp.message(Command("search"))
async def search_anime(message: types.Message):
    """Handles /search command to fetch anime PFPs."""
    query = message.text.replace("/search ", "").strip()
    
    if not query:
        await message.reply("Please enter an anime name! Example: `/search Naruto`")
        return
    
    await message.reply(f"🔍 Searching for `{query}` PFPs... Please wait.")

    images = await fetch_images(query)
    
    if not images:
        await message.reply("❌ No high-quality PFPs found! Try another anime.")
        return

    # Send images one by one
    for img_url in images:
        async with aiohttp.ClientSession() as session:
            async with session.get(img_url) as resp:
                if resp.status == 200:
                    img_data = await resp.read()
                    image = InputFile(BytesIO(img_data), filename="anime_pfp.jpg")
                    await message.answer_photo(photo=image)

# START BOT
async def main():
    print("🤖 YorX PFP Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions

# ➲ ᴍᴀɪɴ ʙᴏᴛ ᴄᴏɴᴛʀᴏʟ
OWNER_ID = 6748827895  # Replace with your Telegram ID
BOT_TOKEN = "YOUR_MAIN_BOT_TOKEN"  # Main bot token
API_ID = 26416419  # Your API ID
API_HASH = "YOUR_API_HASH"  # Your API Hash

app = Client("MainBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ➲ ᴍᴏᴅ ᴜsᴇʀs (sʜᴀᴅᴏᴡs)
shadows = set()
added_bots = {}  # Store added bot tokens

# ➲ **ᴍᴀɴᴜᴀʟ ᴀɴɪᴍᴀᴛᴇᴅ ᴛᴇxᴛ**
async def animate_text(chat_id, text, delay=0.1):
    msg = await app.send_message(chat_id, "...")
    animation = ""
    for letter in text:
        animation += letter
        await msg.edit_text(animation)
        await asyncio.sleep(delay)

# ➲ **ᴡʜᴇɴ ʙᴏᴛ sᴛᴀʀᴛs, ɪᴛ sᴇɴᴅs ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴏᴡɴᴇʀ**
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    start_msg = "**˹ ᴛʜᴇ ᴅᴀʀᴋ ᴏʀᴅᴇʀ ʜᴀs ʀᴇsᴜʀɢᴇᴅ ˼**\n\n"
    start_msg += "➥ /add {ᴛᴏᴋᴇɴ} → ᴀᴅᴅ ᴀ sʟᴀᴠᴇ ʙᴏᴛ\n"
    start_msg += "➥ /addmod {ᴜsᴇʀɴᴀᴍᴇ} → ʀᴀɪsᴇ ᴀ sʜᴀᴅᴏᴡ\n"
    start_msg += "➥ /banall {ᴄʜᴀᴛ} → ᴇʟɪᴍɪɴᴀᴛᴇ ᴇᴠᴇʀʏᴏɴᴇ\n"
    start_msg += "➥ /mute {ᴄʜᴀᴛ} {ᴜsᴇʀ} → ᴘᴜɴɪsʜ ᴛʜᴇ ᴡᴇᴀᴋ\n"
    await animate_text(message.chat.id, start_msg)

# ➲ **ᴀᴅᴅ ᴍᴜʟᴛɪᴘʟᴇ ʙᴏᴛs**
@app.on_message(filters.command("add") & filters.user(OWNER_ID))
async def add_bot(client, message):
    if len(message.command) < 2:
        return await message.reply_text("➥ ᴜsᴀɢᴇ → /add {ᴛᴏᴋᴇɴ}")

    token = message.command[1]
    new_bot = Client(f"bot_{token[:5]}", api_id=API_ID, api_hash=API_HASH, bot_token=token)
    await new_bot.start()
    added_bots[token] = new_bot

    await animate_text(message.chat.id, "➥ ᴛʜᴇ ɴᴇᴡ sʟᴀᴠᴇ ʙᴏᴛ ʜᴀs ʙᴇᴇɴ ʙɪɴᴅᴇᴅ ᴛᴏ ᴛʜᴇ ᴅᴀʀᴋ ᴏʀᴅᴇʀ.")

# ➲ **ᴀᴅᴅ sʜᴀᴅᴏᴡ ᴍᴏᴅs**
@app.on_message(filters.command("addmod") & filters.user(OWNER_ID))
async def add_shadow(client, message):
    if len(message.command) < 2:
        return await message.reply_text("➥ ᴜsᴀɢᴇ → /addmod {ᴜsᴇʀɴᴀᴍᴇ}")

    target_user = message.command[1]
    user = await client.get_users(target_user)
    shadows.add(user.id)
    await animate_text(message.chat.id, f"➥ {user.mention} ʜᴀs ʙᴇᴇɴ ʀᴀɪsᴇᴅ ᴛᴏ ᴛʜᴇ ᴅᴀʀᴋ ᴏʀᴅᴇʀ.")

# ➲ **ʙᴀɴ ᴀʟʟ ᴍᴇᴍʙᴇʀs**
@app.on_message(filters.command("banall") & filters.user(OWNER_ID))
async def ban_all(client, message):
    if len(message.command) < 2:
        return await message.reply_text("➥ ᴜsᴀɢᴇ → /banall {ᴄʜᴀᴛ}")

    chat_username = message.command[1]
    chat = await client.get_chat(chat_username)

    async for member in client.get_chat_members(chat.id):
        if member.user.id != OWNER_ID and member.user.id not in shadows:
            await client.ban_chat_member(chat.id, member.user.id)
    
    await animate_text(message.chat.id, "➥ ᴛʜᴇ ᴏʀᴅᴇʀ ʜᴀs ᴄʟᴇᴀɴsᴇᴅ ᴛʜᴇ ᴅɪsᴏʀᴅᴇʀ.")

# ➲ **ᴍᴜᴛᴇ / ᴜɴᴍᴜᴛᴇ ᴜsᴇʀs**
@app.on_message(filters.command(["mute", "unmute"]) & filters.user(OWNER_ID))
async def mute_unmute(client, message):
    if len(message.command) < 3:
        return await message.reply_text("➥ ᴜsᴀɢᴇ → /mute {ᴄʜᴀᴛ} {ᴜsᴇʀ}")

    chat_username = message.command[1]
    target_user = message.command[2]
    chat = await client.get_chat(chat_username)
    user = await client.get_users(target_user)

    if message.command[0] == "mute":
        await client.restrict_chat_member(chat.id, user.id, ChatPermissions())
        await animate_text(message.chat.id, "➥ ᴛʜᴇɪʀ ᴠᴏɪᴄᴇ ʜᴀs ʙᴇᴇɴ sɪʟᴇɴᴄᴇᴅ.")
    else:
        await client.restrict_chat_member(chat.id, user.id, ChatPermissions(can_send_messages=True))
        await animate_text(message.chat.id, "➥ ᴛʜᴇɪʀ ᴠᴏɪᴄᴇ ʜᴀs ʙᴇᴇɴ ʀᴇsᴛᴏʀᴇᴅ.")

# ➲ **ᴋɪᴄᴋ ᴜsᴇʀ**
@app.on_message(filters.command("kick") & filters.user(OWNER_ID))
async def kick_user(client, message):
    if len(message.command) < 3:
        return await message.reply_text("➥ ᴜsᴀɢᴇ → /kick {ᴄʜᴀᴛ} {ᴜsᴇʀ}")

    chat_username = message.command[1]
    target_user = message.command[2]
    chat = await client.get_chat(chat_username)
    user = await client.get_users(target_user)

    await client.ban_chat_member(chat.id, user.id)
    await animate_text(message.chat.id, "➥ ᴛʜᴇ ᴡᴇᴀᴋ ʜᴀs ʙᴇᴇɴ ᴄᴀsᴛ ᴏᴜᴛ.")

# ➲ **ᴡʜᴇɴ ʙᴏᴛ sᴛᴀʀᴛs**
async def start_bot():
    await app.start()
    await animate_text(OWNER_ID, "➥ ᴛʜᴇ ᴏʀᴅᴇʀ ʜᴀs ʙᴇᴇɴ ᴇsᴛᴀʙʟɪsʜᴇᴅ.")
    await asyncio.Event().wait()

# ➲ **sᴛᴀʀᴛ ʙᴏᴛ**
app.run(start_bot())

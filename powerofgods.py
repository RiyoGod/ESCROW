import asyncio
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions

# ➲ ᴍᴀɪɴ  ʙᴏᴛ ᴄᴏɴᴛʀᴏʟ
OWNER_ID = 6748827895  # Replace with your Telegram ID
BOT_TOKEN = "7648583043:AAEmuvI622knL898njvRDs7-CVjWFjWbNBU"  # Replace with your bot token
API_ID = 26416419  # Replace with your API ID
API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"  # Replace with your API Hash
app = Client("MainBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ➲ ᴍᴏᴅ ᴜsᴇʀs (sʜᴀᴅᴏᴡs)
shadows = set()

# ➲ ᴍᴀɴᴜᴀʟ ᴀɴɪᴍᴀᴛᴇᴅ ᴛᴇxᴛ
async def animate_text(message, text, delay=0.1):
    msg = await message.reply_text("...")
    animation = ""
    for letter in text:
        animation += letter
        await msg.edit_text(animation)
        await asyncio.sleep(delay)
    return msg

# ➲ ᴀᴅᴅ ɴᴇᴡ sʜᴀᴅᴏᴡ (ᴍᴏᴅ)
@app.on_message(filters.command("addmod") & filters.user(OWNER_ID))
async def add_shadow(client, message):
    if len(message.command) < 2:
        return await message.reply_text("➥ ᴜsᴀɢᴇ → /addmod {ᴜsᴇʀɴᴀᴍᴇ}")

    target_user = message.command[1]
    user = await client.get_users(target_user)
    shadows.add(user.id)
    await animate_text(message, f"➥ {user.mention} ʜᴀs ʙᴇᴇɴ ʀᴀɪsᴇᴅ ᴛᴏ ᴛʜᴇ sʜᴀᴅᴏᴡ ʀᴀɴᴋs.")

# ➲ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ɴᴀᴍᴇ & ᴅᴇsᴄʀɪᴘᴛɪᴏɴ
@app.on_message(filters.command("change") & filters.private & (filters.user(OWNER_ID) | filters.user(shadows)))
async def change_group_info(client, message):
    if len(message.command) < 2:
        return await message.reply_text("➥ ᴜsᴀɢᴇ → /change {ᴄʜᴀᴛ.ᴜsᴇʀɴᴀᴍᴇ}")

    chat_username = message.command[1]
    chat = await client.get_chat(chat_username)

    await message.reply_text("➥ ᴇɴᴛᴇʀ ɴᴇᴡ ɢʀᴏᴜᴘ ɴᴀᴍᴇ:")
    group_name = (await client.listen(message.chat.id)).text

    await message.reply_text("➥ ᴇɴᴛᴇʀ ɴᴇᴡ ɢʀᴏᴜᴘ ᴅᴇsᴄʀɪᴘᴛɪᴏɴ:")
    group_desc = (await client.listen(message.chat.id)).text

    await client.set_chat_title(chat.id, group_name)
    await client.set_chat_description(chat.id, group_desc)
    await animate_text(message, "➥ ɢʀᴏᴜᴘ ᴜᴘᴅᴀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.")

# ➲ ʙᴀɴ ᴀʟʟ ᴜsᴇʀs
@app.on_message(filters.command("banall") & (filters.user(OWNER_ID) | filters.user(shadows)))
async def ban_all_members(client, message):
    if len(message.command) < 2:
        return await message.reply_text("➥ ᴜsᴀɢᴇ → /banall {ᴄʜᴀᴛ.ᴜsᴇʀɴᴀᴍᴇ}")

    chat_username = message.command[1]
    chat = await client.get_chat(chat_username)

    async for member in client.get_chat_members(chat.id):
        if member.user.id not in [OWNER_ID, *shadows]:
            await client.ban_chat_member(chat.id, member.user.id)
    await animate_text(message, "➥ ᴀʟʟ ᴇɴᴇᴍɪᴇs ᴇʀᴀᴅɪᴄᴀᴛᴇᴅ.")

# ➲ ʙᴀɴ ᴜsᴇʀ
@app.on_message(filters.command("ban") & (filters.user(OWNER_ID) | filters.user(shadows)))
async def ban_user(client, message):
    if len(message.command) < 3:
        return await message.reply_text("➥ ᴜsᴀɢᴇ → /ban {ᴄʜᴀᴛ.ᴜsᴇʀɴᴀᴍᴇ} {ᴜsᴇʀɴᴀᴍᴇ}")

    chat_username = message.command[1]
    target_user = message.command[2]
    chat = await client.get_chat(chat_username)
    user = await client.get_users(target_user)

    await client.ban_chat_member(chat.id, user.id)
    await animate_text(message, f"➥ {user.mention} ʜᴀs ʙᴇᴇɴ ᴄᴏɴsᴜᴍᴇᴅ ʙʏ ᴛʜᴇ sʜᴀᴅᴏᴡs.")

# ➲ ᴍᴜᴛᴇ / ᴜɴᴍᴜᴛᴇ
@app.on_message(filters.command(["mute", "unmute"]) & (filters.user(OWNER_ID) | filters.user(shadows)))
async def mute_unmute_user(client, message):
    if len(message.command) < 3:
        return await message.reply_text("➥ ᴜsᴀɢᴇ → /mute {ᴄʜᴀᴛ.ᴜsᴇʀɴᴀᴍᴇ} {ᴜsᴇʀɴᴀᴍᴇ}")

    chat_username = message.command[1]
    target_user = message.command[2]
    chat = await client.get_chat(chat_username)
    user = await client.get_users(target_user)

    if message.command[0] == "mute":
        await client.restrict_chat_member(chat.id, user.id, ChatPermissions())
        await animate_text(message, "➥ ᴛʜᴇɪʀ ᴠᴏɪᴄᴇ ʜᴀs ʙᴇᴇɴ sɪʟᴇɴᴄᴇᴅ.")
    else:
        await client.restrict_chat_member(chat.id, user.id, ChatPermissions(can_send_messages=True))
        await animate_text(message, "➥ ᴛʜᴇɪʀ ᴠᴏɪᴄᴇ ʜᴀs ʙᴇᴇɴ ʀᴇsᴛᴏʀᴇᴅ.")

# ➲ ᴋɪᴄᴋ ᴜsᴇʀ
@app.on_message(filters.command("kick") & (filters.user(OWNER_ID) | filters.user(shadows)))
async def kick_user(client, message):
    if len(message.command) < 3:
        return await message.reply_text("➥ ᴜsᴀɢᴇ → /kick {ᴄʜᴀᴛ.ᴜsᴇʀɴᴀᴍᴇ} {ᴜsᴇʀɴᴀᴍᴇ}")

    chat_username = message.command[1]
    target_user = message.command[2]
    chat = await client.get_chat(chat_username)
    user = await client.get_users(target_user)

    await client.ban_chat_member(chat.id, user.id)
    await animate_text(message, "➥ ᴇᴠɪᴄᴛᴇᴅ ᴛʜᴇ ᴡᴇᴀᴋ.")

# ➲ sᴛᴀʀᴛ ʙᴏᴛ
app.run()

import asyncio
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions

# ➲ ᴍᴀɪɴ ʙᴏᴛ ᴄᴏɴᴛʀᴏʟ
OWNER_ID = 6748827895  # Replace with your Telegram ID
BOT_TOKEN = "7648583043:AAEmuvI622knL898njvRDs7-CVjWFjWbNBU"  # Replace with your bot token
app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

api_id = 26416419  # Replace with your actual API ID
api_hash = "c109c77f5823c847b1aeb7fbd4990cc4"  # Replace with your actual API HASH
bot_token = "7648583043:AAEmuvI622knL898njvRDs7-CVjWFjWbNBU"  # Replace with your actual Bot Token



# ➲ sᴛᴏʀᴇ ᴀᴅᴅᴇᴅ ʙᴏᴛs & sʜᴀᴅᴏᴡs
added_bots = {}
shadows = set()

# ➲ ᴍᴀɴᴜᴀʟ ᴀɴɪᴍᴀᴛᴇᴅ ᴛᴇxᴛ ғᴜɴᴄᴛɪᴏɴ
async def animate_text(message, text, delay=0.1):
    msg = await message.reply_text("...")
    animation = ""
    for letter in text:
        animation += letter
        await msg.edit_text(animation)
        await asyncio.sleep(delay)
    return msg

# ➲ sᴛᴀʀᴛ ᴄᴏᴍᴍᴀɴᴅ (ᴀɴɪᴍᴀᴛᴇᴅ)
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    start_msg = "**˹ ᴛʜᴇ sʜᴀᴅᴏᴡ ᴍᴏɴᴀʀᴄʜ ɪs ʜᴇʀᴇ ˼**\n\n"
    start_msg += "➥ /addmod [ᴜsᴇʀ] → ᴀᴅᴅ sʜᴀᴅᴏᴡ\n"
    start_msg += "➥ /change → ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ɴᴀᴍᴇ & ᴅᴇsᴄ\n"
    start_msg += "➥ /banall → ᴇʟɪᴍɪɴᴀᴛᴇ ᴇᴠᴇʀʏᴏɴᴇ\n"
    start_msg += "➥ /mute → ᴘᴜɴɪsʜ ᴛʜᴇ ᴡᴇᴀᴋ\n"
    start_msg += "➥ /unmute → ʀᴇʟᴇᴀsᴇ ᴛʜᴇ ᴄᴜʀsᴇ\n"
    await animate_text(message, start_msg)

# ➲ ᴀᴅᴅ ᴍᴏᴅᴇʀᴀᴛᴏʀ (sʜᴀᴅᴏᴡ)
@app.on_message(filters.command("addmod") & filters.user(OWNER_ID))
async def add_shadow(client, message):
    if not message.reply_to_message:
        return await message.reply_text("➥ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ᴀᴅᴅ ᴛʜᴇᴍ ᴀs ᴀ sʜᴀᴅᴏᴡ.")

    user = message.reply_to_message.from_user
    shadows.add(user.id)
    await animate_text(message, f"➥ {user.mention} ʜᴀs ʙᴇᴇɴ ʀᴀɪsᴇᴅ ᴀs ᴀ sʜᴀᴅᴏᴡ.")

# ➲ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ɴᴀᴍᴇ & ᴅᴇsᴄʀɪᴘᴛɪᴏɴ
@app.on_message(filters.command("change") & filters.private & (filters.user(OWNER_ID) | filters.user(list(shadows))))
async def change_group_info(client, message):
    await message.reply_text("➥ ᴇɴᴛᴇʀ ᴛʜᴇ ɢʀᴏᴜᴘ ɴᴀᴍᴇ:")
    group_name = (await client.listen(message.chat.id)).text

    await message.reply_text("➥ ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴇᴡ ᴅᴇsᴄʀɪᴘᴛɪᴏɴ:")
    group_desc = (await client.listen(message.chat.id)).text

    try:
        await client.set_chat_title(message.chat.id, group_name)
        await client.set_chat_description(message.chat.id, group_desc)
        await animate_text(message, "➥ ɢʀᴏᴜᴘ ᴜᴘᴅᴀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.")
    except:
        await message.reply_text("➥ ғᴀɪʟᴇᴅ ᴛᴏ ᴜᴘᴅᴀᴛᴇ ɢʀᴏᴜᴘ.")

# ➲ ʙᴀɴ ᴀʟʟ ᴜsᴇʀs (ᴏᴡɴᴇʀ + sʜᴀᴅᴏᴡs ᴏɴʟʏ)
@app.on_message(filters.command("banall") & filters.user(OWNER_ID))
async def ban_all_members(client, message):
    chat_id = message.chat.id
    async for member in client.get_chat_members(chat_id):
        if member.user.id != OWNER_ID and member.user.id not in shadows:
            await client.ban_chat_member(chat_id, member.user.id)
    await animate_text(message, "➥ ᴀʟʟ ᴇɴᴇᴍɪᴇs ᴇʀᴀᴅɪᴄᴀᴛᴇᴅ.")

# ➲ ᴍᴜᴛᴇ ᴜsᴇʀ
@app.on_message(filters.command("mute") & filters.user(OWNER_ID))
async def mute_user(client, message):
    if not message.reply_to_message:
        return await message.reply_text("➥ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ᴍᴜᴛᴇ ᴛʜᴇᴍ.")
    
    user_id = message.reply_to_message.from_user.id
    await client.restrict_chat_member(message.chat.id, user_id, ChatPermissions())
    await animate_text(message, "➥ ᴛʜᴇɪʀ ᴠᴏɪᴄᴇ ʜᴀs ʙᴇᴇɴ sɪʟᴇɴᴄᴇᴅ.")

# ➲ ᴜɴᴍᴜᴛᴇ ᴜsᴇʀ
@app.on_message(filters.command("unmute") & filters.user(OWNER_ID))
async def unmute_user(client, message):
    if not message.reply_to_message:
        return await message.reply_text("➥ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ᴜɴᴍᴜᴛᴇ ᴛʜᴇᴍ.")
    
    user_id = message.reply_to_message.from_user.id
    await client.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=True))
    await animate_text(message, "➥ ᴛʜᴇɪʀ ᴠᴏɪᴄᴇ ʜᴀs ʙᴇᴇɴ ʀᴇsᴛᴏʀᴇᴅ.")

# ➲ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ
app.run()

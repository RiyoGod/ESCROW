import asyncio
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions

# ➲ ᴍᴀɪɴ ʙᴏᴛ ᴄᴏɴᴛʀᴏʟ
OWNER_ID = 6748827895  
API_ID = 26416419  
API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"  
BOT_TOKEN = "7648583043:AAEmuvI622knL898njvRDs7-CVjWFjWbNBU"  

app = Client("MainBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ➲ ᴅʏɴᴀᴍɪᴄ ʙᴏᴛ ᴄᴏɴᴛʀᴏʟ
added_bots = {}  
shadows = set()  

# ➲ ᴍᴀɴᴜᴀʟ ᴀɴɪᴍᴀᴛᴇᴅ sᴛᴇᴘ-ʙʏ-sᴛᴇᴘ ᴛᴇxᴛ
async def step_by_step(message, steps, delay=1.5):
    msg = await message.reply_text(steps[0])
    for step in steps[1:]:
        await asyncio.sleep(delay)
        await msg.edit_text(step)
    return msg

# ➲ ʙᴏᴛ ᴀᴅᴅɪɴɢ ᴄᴏᴍᴍᴀɴᴅ (/add {ʙᴏᴛ_ᴛᴏᴋᴇɴ})
@app.on_message(filters.command("add") & filters.user(OWNER_ID))
async def add_bot(client, message):
    if len(message.command) < 2:
        return await message.reply_text("➥ ᴜsᴇ → /add {ʙᴏᴛ_ᴛᴏᴋᴇɴ}")
    
    token = message.command[1]
    try:
        steps = ["ᴀᴅᴅɪɴɢ ʙᴏᴛ...", "ᴀᴅᴅɪɴɢ ʙᴏᴛ.....", "sᴜᴄᴄᴇssғᴜʟʟʏ ᴀᴅᴅᴇᴅ ɴᴏᴡ."]
        await step_by_step(message, steps)

        new_bot = Client(f"bot_{len(added_bots)}", api_id=API_ID, api_hash=API_HASH, bot_token=token)
        added_bots[token] = new_bot
        await new_bot.start()
    except Exception as e:
        await message.reply_text(f"➥ ғᴀɪʟᴇᴅ ᴛᴏ ᴀᴅᴅ ʙᴏᴛ:\n\n{str(e)}")

# ➲ ᴍᴏᴅ ᴜsᴇʀs (sʜᴀᴅᴏᴡs)
@app.on_message(filters.command("addmod") & filters.user(OWNER_ID))
async def add_shadow(client, message):
    if len(message.command) < 2:
        return await message.reply_text("➥ ᴜsᴇ → /addmod {ᴜsᴇʀɴᴀᴍᴇ}")

    target_user = message.command[1]
    user = await client.get_users(target_user)

    steps = [f"ᴇʟᴇᴠᴀᴛɪɴɢ {user.mention}...", "ᴇʟᴇᴠᴀᴛɪɴɢ ᴛᴏ sʜᴀᴅᴏᴡ ʀᴀɴᴋs....", "sᴜᴄᴄᴇssғᴜʟʟʏ ᴍᴀᴅᴇ ᴀ sʜᴀᴅᴏᴡ."]
    await step_by_step(message, steps)

    shadows.add(user.id)

# ➲ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴘ ɴᴀᴍᴇ & ᴅᴇsᴄʀɪᴘᴛɪᴏɴ
@app.on_message(filters.command("change") & filters.private & filters.user([OWNER_ID, *shadows]))
async def change_group_info(client, message):
    if len(message.command) < 2:
        return await message.reply_text("➥ ᴜsᴇ → /change {ᴄʜᴀᴛ.ᴜsᴇʀɴᴀᴍᴇ}")

    chat_username = message.command[1]
    chat = await client.get_chat(chat_username)

    await message.reply_text("➥ ᴇɴᴛᴇʀ ɴᴇᴡ ɢʀᴏᴜᴘ ɴᴀᴍᴇ:")
    group_name = (await client.listen(message.chat.id)).text

    await message.reply_text("➥ ᴇɴᴛᴇʀ ɴᴇᴡ ɢʀᴏᴜᴘ ᴅᴇsᴄʀɪᴘᴛɪᴏɴ:")
    group_desc = (await client.listen(message.chat.id)).text

    steps = ["ᴜᴘᴅᴀᴛɪɴɢ ɢʀᴏᴜᴘ...", "ᴜᴘᴅᴀᴛɪɴɢ ᴛɪᴛʟᴇ ᴀɴᴅ ᴅᴇsᴄʀɪᴘᴛɪᴏɴ...", "ᴄᴏᴍᴘʟᴇᴛᴇ."]
    await step_by_step(message, steps)

    await client.set_chat_title(chat.id, group_name)
    await client.set_chat_description(chat.id, group_desc)

# ➲ ʙᴀɴ ᴀʟʟ ᴜsᴇʀs
@app.on_message(filters.command("banall") & filters.user([OWNER_ID, *shadows]))
async def ban_all_members(client, message):
    if len(message.command) < 2:
        return await message.reply_text("➥ ᴜsᴇ → /banall {ᴄʜᴀᴛ.ᴜsᴇʀɴᴀᴍᴇ}")

    chat_username = message.command[1]
    chat = await client.get_chat(chat_username)

    steps = ["ᴇʟɪᴍɪɴᴀᴛɪɴɢ ᴛʜᴇᴍ...", "ᴘᴜʀɢɪɴɢ ᴇɴᴛɪʀᴇ ᴄʜᴀᴛ...", "ᴀʟʟ ᴇɴᴇᴍɪᴇs ᴇʀᴀᴅɪᴄᴀᴛᴇᴅ."]
    await step_by_step(message, steps)

    async for member in client.get_chat_members(chat.id):
        if member.user.id not in [OWNER_ID, *shadows]:
            await client.ban_chat_member(chat.id, member.user.id)

# ➲ ᴋɪᴄᴋ ᴜsᴇʀ
@app.on_message(filters.command("kick") & filters.user([OWNER_ID, *shadows]))
async def kick_user(client, message):
    if len(message.command) < 3:
        return await message.reply_text("➥ ᴜsᴇ → /kick {ᴄʜᴀᴛ.ᴜsᴇʀɴᴀᴍᴇ} {ᴜsᴇʀɴᴀᴍᴇ}")

    chat_username = message.command[1]
    target_user = message.command[2]
    chat = await client.get_chat(chat_username)
    user = await client.get_users(target_user)

    steps = ["ᴛᴀʀɢᴇᴛɪɴɢ ᴛʜᴇ ᴇɴᴇᴍʏ...", "ᴇxᴇᴄᴜᴛɪɴɢ ᴇxᴘᴜʟsɪᴏɴ...", "ᴛʜᴇʏ ᴀʀᴇ ɴᴏ ᴍᴏʀᴇ."]
    await step_by_step(message, steps)

    await client.ban_chat_member(chat.id, user.id)

# ➲ sᴛᴀʀᴛ ʙᴏᴛ
app.run()

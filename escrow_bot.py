import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from config import TOKEN, LOGS_CHAT_ID, ADMINS

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, parse_mode="Markdown")
dp = Dispatcher()

# Deal Storage (temporary)
deals = {}

@dp.message(Command("create"))
async def create_command(message: types.Message):
    if message.chat.type != "supergroup" and message.chat.type != "group":
        return await message.reply("This command only works inside a group.")
    
    await message.reply("Fill this form:\n\n"
                        "`Seller : @seller_username`\n"
                        "`Buyer : @buyer_username`\n"
                        "`Deal Info :`\n"
                        "`Amount (In USDT) :`\n"
                        "`Time To Complete :`")

@dp.message(F.reply_to_message)
async def handle_form_submission(message: types.Message):
    if message.reply_to_message.text and "Fill this form" in message.reply_to_message.text:
        lines = message.text.split("\n")
        if len(lines) < 5:
            return await message.reply("Please fill all the fields properly.")

        form_data = {}
        for line in lines:
            key, value = line.split(":", 1)
            form_data[key.strip()] = value.strip()

        seller = form_data.get("Seller").replace("@", "")
        buyer = form_data.get("Buyer").replace("@", "")
        deal_id = f"ESCROW-{message.chat.id}-{message.message_id}"

        deals[deal_id] = {
            "seller": seller,
            "buyer": buyer,
            "confirmed": {"seller": False, "buyer": False},
            "amount": float(form_data.get("Amount (In USDT)", 0)),
            "fees": 0,
            "form": message.text,
            "chat_id": message.chat.id,
            "form_message_id": message.message_id
        }

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{seller} ❄ @{seller} ❄", callback_data=f"confirm:seller:{deal_id}")],
            [InlineKeyboardButton(text=f"{buyer} ❄ @{buyer} ❄", callback_data=f"confirm:buyer:{deal_id}")]
        ])

        confirmation_msg = (
            f"✅ Form received!\n\n"
            f"{message.text}\n\n"
            "Both of you confirm your roles below:"
        )

        sent_msg = await message.reply(confirmation_msg, reply_markup=keyboard)

        deals[deal_id]["form_message_id"] = sent_msg.message_id

        # Notify admins in logs group
        await bot.send_message(LOGS_CHAT_ID, f"New Deal Form Submitted in {message.chat.title}\n\n{message.text}")

@dp.callback_query(F.data.startswith("confirm"))
async def confirm_callback(query: types.CallbackQuery):
    _, role, deal_id = query.data.split(":")
    deal = deals.get(deal_id)

    if not deal:
        return await query.answer("This deal no longer exists.")

    user = query.from_user.username
    allowed_user = deal[role]
    if user != allowed_user:
        return await query.answer(f"Only @{allowed_user} can confirm this.")

    if deal["confirmed"][role]:
        return await query.answer(f"{role.capitalize()} already confirmed.")

    deal["confirmed"][role] = True
    await query.answer(f"{role.capitalize()} confirmed the deal!")

    if all(deal["confirmed"].values()):
        await ask_fees(query.message.chat.id, deal_id)
    else:
        await bot.send_message(query.message.chat.id, f"✅ @{user} confirmed as {role}. Waiting for the other party.")

async def ask_fees(chat_id, deal_id):
    deal = deals[deal_id]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Mine (I Pay Full Fees)", callback_data=f"fees:mine:{deal_id}")],
        [InlineKeyboardButton(text="Split (Both Pay 50%)", callback_data=f"fees:split:{deal_id}")]
    ])
    await bot.send_message(chat_id, "Who will pay the escrow fees (2%)?", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("fees"))
async def fees_callback(query: types.CallbackQuery):
    _, option, deal_id = query.data.split(":")
    deal = deals.get(deal_id)

    if not deal:
        return await query.answer("This deal no longer exists.")

    user = query.from_user.username
    if user not in [deal["seller"], deal["buyer"]]:
        return await query.answer("Only buyer or seller can choose fees option.")

    if "fees_chosen" in deal:
        return await query.answer("Fees option already chosen.")

    deal["fees_chosen"] = option
    amount = deal["amount"]
    fee = amount * 0.02

    if option == "mine":
        payer = user
        msg = f"✅ @{payer} chose to pay full fees ({fee} USDT)."
    else:
        payer = "both"
        msg = f"✅ Both will split the fees ({fee / 2:.2f} USDT each)."

    deal["fees"] = fee
    await query.message.edit_text(msg)

    final_confirm_message = (
        f"✅ Deal Confirmed!\n\n"
        f"{deal['form']}\n\n"
        f"Escrow Fee: {fee} USDT ({option.capitalize()})\n"
        f"Status: *Ongoing Deal*\n"
        f"Escrow ID: `{deal_id}`"
    )

    pinned_msg = await bot.send_message(deal["chat_id"], final_confirm_message)
    await bot.pin_chat_message(deal["chat_id"], pinned_msg.message_id)

    # Notify logs group
    await bot.send_message(LOGS_CHAT_ID, f"✅ Deal Confirmed in {query.message.chat.title}\n\n{final_confirm_message}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

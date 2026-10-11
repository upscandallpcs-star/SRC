import asyncio
import math
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, ADMINS, OWNER_HANDLE, SUPPORT_GROUP
from db import db

# pyromod इम्पोर्ट ताकि ask() बिना एरर के चले
import pyromod

class Bot(Client):
    def __init__(self):
        super().__init__(
            "SACHIN_SHARMA",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="TechVJ"),
            workers=150,
            sleep_threshold=5
        )

    async def start(self):
        await super().start()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("SACHIN SHARMA Bot Started Successfully!")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    async def stop(self, *args):
        await super().stop()
        print("SACHIN SHARMA Bot Stopped.")

bot = Bot()

# ----------------- PROGRESS HELPER ----------------- #
def humanbytes(size):
    if not size:
        return "0 B"
    power = 1024
    t_n = 0
    power_labels = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        t_n += 1
    return f"{round(size, 2)} {power_labels[t_n]}B"

def time_formatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s") if seconds else "")
    return tmp if tmp else "0s"

# ----------------- USER COMMANDS ----------------- #
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    db.add_user(user_id, name)

    text = (
        f"👋 नमस्ते **{name}**!\n\n"
        f"यह **SACHIN SHARMA** सेव रेस्ट्रिक्टेड कंटेंट बॉट है।\n"
        f"यहाँ आप किसी भी रेस्ट्रिक्टेड चैनल/ग्रुप से फाइल डाउनलोड कर सकते हैं।\n\n"
        f"⚠️ **नोट:** यह एक प्राइवेट बॉट है। इसे इस्तेमाल करने के लिए आपके पास एक्टिव पेड प्लान होना ज़रूरी है।\n\n"
        f"🔹 प्लान देखने के लिए: /plans\n"
        f"🔹 अकाउंट जोड़ने के लिए: /login\n"
        f"🔹 कंटेंट डाउनलोड करने के लिए: /clone\n"
        f"🔹 मदद के लिए: /help"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 सपोर्ट ग्रुप", url=SUPPORT_GROUP)],
        [InlineKeyboardButton("👤 ओनर से संपर्क करें", url=f"https://t.me/{OWNER_HANDLE.replace('@', '')}")]
    ])
    await message.reply_text(text, reply_markup=buttons, disable_web_page_preview=True)

@bot.on_message(filters.command("id"))
async def get_id(client: Client, message: Message):
    if message.reply_to_message:
        text = f"👤 User ID: `{message.reply_to_message.from_user.id}`\n"
        if message.reply_to_message.forward_from_chat:
            text += f"📢 Channel/Chat ID: `{message.reply_to_message.forward_from_chat.id}`"
        await message.reply_text(text)
    else:
        await message.reply_text(f"👉 आपकी Telegram ID है: `{message.from_user.id}`")

@bot.on_message(filters.command("plans") & filters.private)
async def show_plans(client: Client, message: Message):
    config = db.get_plan_config()
    text = (
        f"💎 **VIP UNLIMITED PLAN** 💎\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 **कीमत:** ₹{config['plan_price']}\n"
        f"⏱️ **वैधता:** {config['plan_days']} दिन\n"
        f"📦 **लिमिट:** अनलिमिटेड फाइल्स और वीडियो\n"
        f"⚡ **स्पीड:** फुल हाई स्पीड\n"
        f"🔄 **फीचर्स:** ऑटो-रिज्यूम और प्राइवेट चैनल सपोर्ट\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👉 प्लान खरीदने के लिए संपर्क करें: {OWNER_HANDLE}\n"
        f"💬 सपोर्ट ग्रुप: [यहाँ जुड़ें]({SUPPORT_GROUP})"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 अभी खरीदें", url=f"https://t.me/{OWNER_HANDLE.replace('@', '')}")],
        [InlineKeyboardButton("💬 सपोर्ट ग्रुप", url=SUPPORT_GROUP)]
    ])
    await message.reply_text(text, reply_markup=buttons, disable_web_page_preview=True)

@bot.on_message(filters.command(["myplan", "info"]) & filters.private)
async def my_plan(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id == ADMINS:
        return await message.reply_text("👑 आप इस बॉट के **ओनर/एडमिन** हैं (लाइफटाइम अनलिमिटेड एक्सेस)।")

    user = db.get_user(user_id)
    if not user or not user.get("plan_expiry"):
        return await message.reply_text("❌ आपके पास कोई एक्टिव प्लान नहीं है।\nप्लान देखने के लिए /plans दबाएँ।")

    expiry = user["plan_expiry"][:19].replace("T", " ")
    await message.reply_text(
        f"👤 **आपकी प्लान जानकारी:**\n\n"
        f"🆔 User ID: `{user_id}`\n"
        f"📊 स्टेटस: **VIP Member**\n"
        f"⏳ एक्सपायरी डेट: `{expiry} UTC`\n\n"
        f"सपोर्ट: {OWNER_HANDLE}"
    )

# ----------------- ADMIN COMMANDS ----------------- #
@bot.on_message(filters.command("setplan") & filters.user(ADMINS))
async def set_plan_admin(client: Client, message: Message):
    try:
        parts = message.text.split()
        if len(parts) != 3:
            return await message.reply_text("❌ गलत फॉर्मेट!\nउदाहरण: `/setplan 150 15` (प्राइस दिन)")
        price = parts[1]
        days = parts[2]
        db.set_plan_config(price, days)
        await message.reply_text(f"✅ **नया प्लान सेट हो गया:**\nकीमत: ₹{price}\nवैधता: {days} दिन")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@bot.on_message(filters.command("adduser") & filters.user(ADMINS))
async def add_user_admin(client: Client, message: Message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            return await message.reply_text("❌ गलत फॉर्मेट!\nउदाहरण: `/adduser 123456789` या `/adduser 123456789 30`")
        target_id = int(parts[1])
        config = db.get_plan_config()
        days = int(parts[2]) if len(parts) > 2 else int(config['plan_days'])

        db.add_vip_user(target_id, days)
        await message.reply_text(f"✅ यूजर `{target_id}` को **{days} दिन** के लिए VIP एक्सेस दे दिया गया है।")
        try:
            await client.send_message(
                target_id,
                f"🎉 **बधाई हो!** आपका VIP सब्सक्रिप्शन एक्टिवेट कर दिया गया है ({days} दिन के लिए)।\nअब आप बॉट का इस्तेमाल कर सकते हैं।"
            )
        except Exception:
            pass
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@bot.on_message(filters.command("removeuser") & filters.user(ADMINS))
async def remove_user_admin(client: Client, message: Message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            return await message.reply_text("❌ गलत फॉर्मेट!\nउदाहरण: `/removeuser 123456789`")
        target_id = int(parts[1])
        db.remove_vip_user(target_id)
        await message.reply_text(f"🚫 यूजर `{target_id}` का VIP एक्सेस हटा दिया गया है।")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

# ----------------- MAIN RUNNER ----------------- #
async def main():
    await bot.start()
    print("Bot is fully running!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

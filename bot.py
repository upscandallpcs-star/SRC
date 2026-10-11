import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from config import API_ID, API_HASH, BOT_TOKEN, ADMINS, OWNER_HANDLE, SUPPORT_GROUP
from db import db

try:
    import pyromod
except ImportError:
    pass

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

# ----------------- ADMIN FILTER HELPER ----------------- #
def is_admin(user_id: int) -> bool:
    if isinstance(ADMINS, list):
        return int(user_id) in [int(x) for x in ADMINS]
    return int(user_id) == int(ADMINS)

# ----------------- USER COMMANDS ----------------- #
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    db.add_user(user_id, name)

    admin_badge = "\n👑 **(आप इस बॉट के ओनर हैं - लाइफटाइम एक्सेस)**\n" if is_admin(user_id) else ""

    text = (
        f"👋 नमस्ते **{name}**!{admin_badge}\n\n"
        f"यह **SACHIN SHARMA** सेव रेस्ट्रिक्टेड कंटेंट बॉट है।\n"
        f"यहाँ आप किसी भी रेस्ट्रिक्टेड चैनल/ग्रुप से फाइल डाउनलोड और क्लोन कर सकते हैं।\n\n"
        f"⚠️ **नोट:** यह एक प्राइवेट बॉट है। इसे इस्तेमाल करने के लिए एक्टिव पेड प्लान होना ज़रूरी है।\n\n"
        f"🔹 प्लान देखने के लिए: /plans\n"
        f"🔹 अपना स्टेटस चेक करें: /myplan\n"
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
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else (message.sender_chat.id if message.sender_chat else "Unknown")
    response = f"📍 **चैट/ग्रुप ID:** `{chat_id}`\n👤 **आपकी ID:** `{user_id}`"
    
    if message.reply_to_message:
        rep = message.reply_to_message
        rep_user = rep.from_user.id if rep.from_user else (rep.sender_chat.id if rep.sender_chat else "Anonymous")
        response += f"\n\n↩️ **रिप्लाई यूजर ID:** `{rep_user}`"
        if rep.forward_from_chat:
            response += f"\n📢 **फॉरवर्ड चैट ID:** `{rep.forward_from_chat.id}`"
            
    await message.reply_text(response)

@bot.on_message(filters.command("plans") & filters.private)
async def show_plans(client: Client, message: Message):
    user_id = message.from_user.id
    config = db.get_plan_config()
    
    owner_info = "\n👑 *आप ओनर हैं, आपको प्लान खरीदने की ज़रूरत नहीं है।* \n" if is_admin(user_id) else ""

    text = (
        f"💎 **VIP UNLIMITED CLONER PLAN** 💎\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 **कीमत:** ₹{config['plan_price']}\n"
        f"⏱️ **वैधता:** {config['plan_days']} दिन\n"
        f"📦 **लिमिट:** अनलिमिटेड फाइल्स, वीडियो और PDFs\n"
        f"⚡ **स्पीड:** फुल हाई स्पीड क्लाउड ट्रांसफर\n\n"
        f"🔥 **शामिल प्रीमियम फीचर्स:**\n"
        f"✅ प्राइवेट, पब्लिक व बॉट चैट सपोर्ट\n"
        f"✅ टॉपिक/फोरम ग्रुप्स (Topic Groups) सपोर्ट\n"
        f"✅ ऑटो-कैप्शन रिप्लेस (किसी का भी नाम हटाकर अपना नाम लगाएं)\n"
        f"✅ कस्टम थंबनेल जोड़ने की सुविधा\n"
        f"✅ सीधे अपने चैनल/ग्रुप में ऑटो-अपलोड\n"
        f"✅ लाइव प्रोग्रेस बार (स्पीड, ETA, फ़ाइल नेम ट्रैकिंग)\n"
        f"━━━━━━━━━━━━━━━━━━━━{owner_info}\n"
        f"👉 प्लान एक्टिवेट कराने के लिए संपर्क करें: {OWNER_HANDLE}\n"
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
    if is_admin(user_id):
        return await message.reply_text("👑 आप इस बॉट के **ओनर/एडमिन** हैं (लाइफटाइम अनलिमिटेड VIP एक्सेस)।")

    user = db.get_user(user_id)
    if not user or not user.get("plan_expiry"):
        return await message.reply_text("❌ आपके पास कोई एक्टिव प्लान नहीं है।\nप्लान देखने के लिए /plans दबाएँ।")

    expiry = user["plan_expiry"][:19].replace("T", " ")
    await message.reply_text(
        f"👤 **आपकी प्लान जानकारी:**\n\n"
        f"🆔 User ID: `{user_id}`\n"
        f"📊 स्टेटस: **VIP Member ✅**\n"
        f"⏳ एक्सपायरी डेट: `{expiry} UTC`\n\n"
        f"सपोर्ट: {OWNER_HANDLE}"
    )

# ----------------- OWNER / ADMIN COMMANDS ----------------- #
@bot.on_message(filters.command("setplan") & filters.private)
async def set_plan_admin(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return
    try:
        parts = message.text.split()
        if len(parts) != 3:
            return await message.reply_text("❌ गलत फॉर्मेट!\nउदाहरण: `/setplan 149 15` (कीमत दिन)")
        price = parts[1]
        days = parts[2]
        db.set_plan_config(price, days)
        await message.reply_text(f"✅ **नया प्लान सेट हो गया:**\nकीमत: ₹{price}\nवैधता: {days} दिन")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@bot.on_message(filters.command("adduser") & filters.private)
async def add_user_admin(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            return await message.reply_text("❌ गलत फॉर्मेट!\nउदाहरण: `/adduser 123456789 30`")
        target_id = int(parts[1])
        config = db.get_plan_config()
        days = int(parts[2]) if len(parts) > 2 else int(config['plan_days'])

        db.add_vip_user(target_id, days)
        await message.reply_text(f"✅ यूजर `{target_id}` को **{days} दिन** के लिए VIP एक्सेस दे दिया गया है।")
        try:
            await client.send_message(
                target_id,
                f"🎉 **बधाई हो!** आपका VIP सब्सक्रिप्शन एक्टिवेट कर दिया गया है ({days} दिन के लिए)।\nअब आप /clone का उपयोग कर सकते हैं।"
            )
        except Exception:
            pass
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@bot.on_message(filters.command("removeuser") & filters.private)
async def remove_user_admin(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return
    try:
        parts = message.text.split()
        if len(parts) != 2:
            return await message.reply_text("❌ गलत फॉर्मेट!\nउदाहरण: `/removeuser 123456789`")
        target_id = int(parts[1])
        db.remove_vip_user(target_id)
        await message.reply_text(f"🚫 यूजर `{target_id}` का VIP एक्सेस हटा दिया गया है।")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

# ----------------- BROADCAST COMMAND ----------------- #
@bot.on_message(filters.command("broadcast") & filters.private)
async def broadcast_command(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return

    if not message.reply_to_message:
        return await message.reply_text("⚠️ **इस्तेमाल का तरीका:** जिस मैसेज को सभी यूज़र्स को भेजना है, उस पर रिप्लाई करके `/broadcast` लिखें।")

    users = db.get_all_users()
    total_users = len(users)
    if total_users == 0:
        return await message.reply_text("❌ डेटाबेस में कोई यूज़र नहीं मिला।")

    b_msg = await message.reply_text(f"📢 **ब्रॉडकास्ट शुरू हो रहा है...**\nकुल यूज़र्स: `{total_users}`")

    success = 0
    blocked = 0
    failed = 0

    for user in users:
        u_id = user["user_id"]
        try:
            await message.reply_to_message.copy(u_id)
            success += 1
        except FloodWait as f:
            await asyncio.sleep(f.value)
            try:
                await message.reply_to_message.copy(u_id)
                success += 1
            except Exception:
                failed += 1
        except (UserIsBlocked, InputUserDeactivated):
            blocked += 1
        except Exception:
            failed += 1

        await asyncio.sleep(0.05)

    await b_msg.edit_text(
        f"✅ **ब्रॉडकास्ट पूरा हुआ!**\n━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 कुल यूज़र्स: `{total_users}`\n"
        f"✔️ सफल: `{success}`\n"
        f"🚫 बॉट ब्लॉक किया: `{blocked}`\n"
        f"❌ असफल: `{failed}`"
    )

# ----------------- RUNNER ----------------- #
if __name__ == "__main__":
    bot.run()

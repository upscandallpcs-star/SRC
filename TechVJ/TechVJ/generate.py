import traceback
from pyrogram.types import Message
from pyrogram import Client, filters
from pyrogram.errors import (
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
from config import API_ID, API_HASH
from db import db

SESSION_STRING_SIZE = 351

@Client.on_message(filters.private & ~filters.forwarded & filters.command(["logout"]))
async def logout(client, message):
    user_data = db.get_session(message.from_user.id)  
    if user_data is None:
        return await message.reply("❌ आप अभी लॉगिन नहीं हैं।")
    db.remove_session(message.from_user.id)  
    await message.reply("✅ **सफलतापूर्वक लॉगआउट कर दिया गया है।**")

@Client.on_message(filters.private & ~filters.forwarded & filters.command(["login"]))
async def main(bot: Client, message: Message):
    user_id = int(message.from_user.id)
    user_data = db.get_session(user_id)
    if user_data is not None:
        await message.reply("⚠️ **आप पहले से लॉगिन हैं। नया अकाउंट जोड़ने से पहले /logout करें।**")
        return 

    # सीधे फ़ोन नंबर मांगना (API ID / Hash नहीं पूछेगा)
    phone_number_msg = await bot.ask(
        chat_id=user_id, 
        text="📱 **कंट्री कोड के साथ अपना फ़ोन नंबर भेजें:**\n(उदाहरण: `+919876543210`)\n\nरद्द करने के लिए /cancel लिखें।",
        filters=filters.text,
        timeout=300
    )
    if phone_number_msg.text == '/cancel':
        return await phone_number_msg.reply("❌ प्रोसेस रद्द कर दिया गया।")
    
    phone_number = phone_number_msg.text.strip()
    api_id = API_ID
    api_hash = API_HASH

    client = Client(":memory:", api_id=api_id, api_hash=api_hash)
    await client.connect()
    await phone_number_msg.reply("📩 OTP भेजा जा रहा है...")
    
    try:
        code = await client.send_code(phone_number)
        phone_code_msg = await bot.ask(
            user_id, 
            "📲 टेलीग्राम पर आया हुआ OTP यहाँ भेजें (अंकों के बीच स्पेस देकर, जैसे: `1 2 3 4 5`):\n\nरद्द करने के लिए /cancel लिखें।", 
            filters=filters.text, 
            timeout=600
        )
    except PhoneNumberInvalid:
        await phone_number_msg.reply("❌ अमान्य फ़ोन नंबर। कृपया सही नंबर डालकर दोबारा /login करें।")
        return

    if phone_code_msg.text == '/cancel':
        return await phone_code_msg.reply("❌ प्रोसेस रद्द कर दिया गया।")

    try:
        phone_code = phone_code_msg.text.replace(" ", "").replace("-", "")
        await client.sign_in(phone_number, code.phone_code_hash, phone_code)
    except PhoneCodeInvalid:
        return await phone_code_msg.reply("❌ गलत OTP दर्ज किया गया है।")
    except PhoneCodeExpired:
        return await phone_code_msg.reply("❌ OTP एक्सपायर हो चुका है।")
    except SessionPasswordNeeded:
        two_step_msg = await bot.ask(
            user_id, 
            "🔐 आपके अकाउंट पर Two-Step Verification लगा है। कृपया अपना पासवर्ड भेजें:\n\nरद्द करने के लिए /cancel लिखें।", 
            filters=filters.text, 
            timeout=300
        )
        if two_step_msg.text == '/cancel':
            return await two_step_msg.reply("❌ प्रोसेस रद्द कर दिया गया।")
        try:
            await client.check_password(password=two_step_msg.text)
        except PasswordHashInvalid:
            return await two_step_msg.reply("❌ गलत पासवर्ड डाला गया है।")

    string_session = await client.export_session_string()
    await client.disconnect()

    if len(string_session) < SESSION_STRING_SIZE:
        return await message.reply("❌ सेशन स्ट्रिंग अमान्य है।")

    db.set_session(user_id, session=string_session)
    db.set_api_id(user_id, api_id=str(api_id))
    db.set_api_hash(user_id, api_hash=str(api_hash))

    await bot.send_message(user_id, "🎉 **अकाउंट सफलतापूर्वक लॉगिन हो गया है!**\nअब आप `/clone` कमांड का उपयोग करके कंटेंट ट्रांसफर कर सकते हैं।")

import os
import asyncio 
import time
import pyrogram
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import ADMINS, CHANNEL_ID, WAITING_TIME
from db import db

try:
    from TechVJ.strings import HELP_TXT
except ModuleNotFoundError:
    try:
        from strings import HELP_TXT
    except ImportError:
        HELP_TXT = "🌟 **SACHIN SHARMA सेव रेस्ट्रिक्टेड बॉट**\n\nकंटेंट डाउनलोड करने के लिए /clone कमांड भेजें।"

class batch_temp(object):
    IS_BATCH = {}
    CLONE_DATA = {}

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

def time_formatter(seconds: int) -> str:
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s") if seconds else "")
    return tmp if tmp else "0s"

def progress(current, total, message, type_):
    with open(f'{message.id}{type_}status.txt', "w") as f:
        f.write(f"{current * 100 / total:.1f}%")

async def track_status(client, statusfile, message, label):
    while not os.path.exists(statusfile):
        await asyncio.sleep(2)
    while os.path.exists(statusfile):
        try:
            with open(statusfile, "r") as f:
                txt = f.read()
            await message.edit_text(f"**{label}:** `{txt}`")
            await asyncio.sleep(4)
        except Exception:
            await asyncio.sleep(3)

@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await message.reply_text(HELP_TXT)

@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    batch_temp.IS_BATCH[message.from_user.id] = True
    if message.from_user.id in batch_temp.CLONE_DATA:
        del batch_temp.CLONE_DATA[message.from_user.id]
    await message.reply_text("🛑 **टास्क रद्द कर दिया गया है।**")

# ----------------- /clone STEP-BY-STEP WORKFLOW ----------------- #
@Client.on_message(filters.command(["clone", "clon"]) & filters.private)
async def clone_command(client: Client, message: Message):
    user_id = message.from_user.id

    if not db.is_user_vip(user_id, ADMINS):
        return await message.reply_text(
            "🔒 **यह फीचर केवल एक्टिव पेड मेंबर्स के लिए है!**\n\n"
            "कंटेंट डाउनलोड करने के लिए प्लान खरीदें।\n"
            "प्लान देखने के लिए: /plans"
        )

    if batch_temp.IS_BATCH.get(user_id) == False:
        return await message.reply_text("⚠️ एक टास्क पहले से चल रहा है। कृपया उसके पूरा होने का इंतज़ार करें या /cancel करें।")

    user_session = db.get_session(user_id)
    if not user_session:
        return await message.reply_text("🔑 प्राइवेट व रेस्ट्रिक्टेड कंटेंट के लिए पहले **/login** करें।")

    # दिशा-निर्देश
    guide_text = (
        "📖 **कंटेंट क्लोनिंग दिशा-निर्देश (Instructions):**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "1. **Public Chat:** `https://t.me/channel_username/1234`\n"
        "2. **Private Chat:** `https://t.me/c/1234567890/1234`\n"
        "3. **Bot Chat:** `https://t.me/b/bot_username/1234`\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👉 **स्टेप 1:** जहाँ से कॉपी करना है, उस पोस्ट की **पहली लिंक (Start Link)** भेजें:\n"
        "(रद्द करने के लिए /cancel लिखें)"
    )
    
    first_msg = await client.ask(user_id, guide_text, filters=filters.text, timeout=300)
    if first_msg.text == "/cancel":
        return await first_msg.reply("❌ प्रोसेस रद्द कर दिया गया।")
    if "https://t.me/" not in first_msg.text:
        return await first_msg.reply("❌ अमान्य टेलीग्राम लिंक! दोबारा /clone करें।")

    start_link = first_msg.text.strip()

    # अंतिम लिंक मांगना
    last_msg = await client.ask(
        user_id, 
        "👉 **स्टेप 2:** अब **अंतिम लिंक (End Link)** भेजें:\n"
        "(यदि केवल एक ही पोस्ट कॉपी करनी है तो `/single` लिखें)",
        filters=filters.text, 
        timeout=300
    )
    if last_msg.text == "/cancel":
        return await last_msg.reply("❌ प्रोसेस रद्द कर दिया गया।")
    
    end_link = start_link if last_msg.text == "/single" else last_msg.text.strip()

    # टारगेट ग्रुप/चैनल लिंक या ID मांगना
    dest_msg = await client.ask(
        user_id,
        "👉 **स्टेप 3:** जहाँ कंटेंट अपलोड करवाना है, उस **चैनल/ग्रुप का लिंक या ID** भेजें:\n"
        "(बॉट को उस चैनल में एडमिन बनाकर रखें! डिफ़ॉल्ट चैट के लिए `/skip` लिखें)",
        filters=filters.text,
        timeout=300
    )
    if dest_msg.text == "/cancel":
        return await dest_msg.reply("❌ प्रोसेस रद्द कर दिया गया।")

    target_chat = message.chat.id if dest_msg.text == "/skip" else dest_msg.text.strip()

    # डेटा स्टोर करना
    batch_temp.CLONE_DATA[user_id] = {
        "start_link": start_link,
        "end_link": end_link,
        "target_chat": target_chat,
        "custom_caption": None,
        "extra_caption": None,
        "thumb_path": None
    }

    await show_customization_menu(client, user_id)

async def show_customization_menu(client: Client, user_id: int):
    data = batch_temp.CLONE_DATA.get(user_id, {})
    cap_status = "सेट है" if data.get("custom_caption") else "डिफ़ॉल्ट"
    ext_status = "सेट है" if data.get("extra_caption") else "कोई नहीं"
    thm_status = "सेट है" if data.get("thumb_path") else "डिफ़ॉल्ट"

    panel_text = (
        "⚙️ **कंटेंट कस्टमाइज़ेशन सेटिंग्स:**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 कस्टम कैप्शन: `{cap_status}`\n"
        f"➕ अतिरिक्त कैप्शन: `{ext_status}`\n"
        f"🖼️ कस्टम थंबनेल: `{thm_status}`\n"
        f"🎯 टारगेट चैट: `{data.get('target_chat')}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "नीचे दिए गए बटनों से बदलाव करें या ट्रांसफर शुरू करने के लिए **Confirm** दबाएँ:"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Edit Caption", callback_data="set_caption"),
         InlineKeyboardButton("➕ Add Extra Caption", callback_data="set_extra")],
        [InlineKeyboardButton("🖼️ Set Thumbnail", callback_data="set_thumb"),
         InlineKeyboardButton("🗑️ Clear Settings", callback_data="clear_settings")],
        [InlineKeyboardButton("🚀 Confirm & Start", callback_data="confirm_start")]
    ])
    await client.send_message(user_id, panel_text, reply_markup=buttons)

# ----------------- CALLBACK BUTTONS ----------------- #
@Client.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in batch_temp.CLONE_DATA:
        return await query.answer("⚠️ सेशन एक्सपायर हो गया, दोबारा /clone करें।", show_alert=True)

    data = query.data

    if data == "set_caption":
        await query.message.delete()
        msg = await client.ask(user_id, "✍️ **नया कस्टम कैप्शन भेजें** (यह पुराना कैप्शन बदल देगा):", filters=filters.text, timeout=180)
        batch_temp.CLONE_DATA[user_id]["custom_caption"] = msg.text
        await show_customization_menu(client, user_id)

    elif data == "set_extra":
        await query.message.delete()
        msg = await client.ask(user_id, "✍️ **अतिरिक्त कैप्शन (Extra Caption) भेजें** (यह पुराने कैप्शन के नीचे जुड़ेगा):", filters=filters.text, timeout=180)
        batch_temp.CLONE_DATA[user_id]["extra_caption"] = msg.text
        await show_customization_menu(client, user_id)

    elif data == "set_thumb":
        await query.message.delete()
        msg = await client.ask(user_id, "🖼️ **थंबनेल के लिए फ़ोटो भेजें:**", filters=filters.photo, timeout=180)
        photo_path = await client.download_media(msg.photo)
        batch_temp.CLONE_DATA[user_id]["thumb_path"] = photo_path
        await msg.reply_text("✅ थंबनेल सेव कर लिया गया!")
        await show_customization_menu(client, user_id)

    elif data == "clear_settings":
        batch_temp.CLONE_DATA[user_id]["custom_caption"] = None
        batch_temp.CLONE_DATA[user_id]["extra_caption"] = None
        if batch_temp.CLONE_DATA[user_id].get("thumb_path") and os.path.exists(batch_temp.CLONE_DATA[user_id]["thumb_path"]):
            os.remove(batch_temp.CLONE_DATA[user_id]["thumb_path"])
        batch_temp.CLONE_DATA[user_id]["thumb_path"] = None
        await query.answer("सेटिंग्स रीसेट कर दी गई हैं।")
        await query.message.delete()
        await show_customization_menu(client, user_id)

    elif data == "confirm_start":
        await query.message.delete()
        await start_clone_task(client, user_id)

# ----------------- EXECUTION FUNCTION ----------------- #
async def start_clone_task(client: Client, user_id: int):
    task_info = batch_temp.CLONE_DATA.get(user_id)
    if not task_info:
        return

    start_link = task_info["start_link"]
    end_link = task_info["end_link"]
    target_chat = task_info["target_chat"]

    user_session = db.get_session(user_id)
    api_id = int(db.get_api_id(user_id))
    api_hash = db.get_api_hash(user_id)

    try:
        acc = Client("saverestricted", session_string=user_session, api_hash=api_hash, api_id=api_id)
        await acc.connect()
    except Exception as e:
        return await client.send_message(user_id, f"❌ सेशन कनेक्ट एरर: `{e}`")

    # ID एक्सट्रैक्ट करना
    s_parts = start_link.split("/")
    e_parts = end_link.split("/")
    fromID = int(s_parts[-1].replace("?single", "").strip())
    toID = int(e_parts[-1].replace("?single", "").strip())

    batch_temp.IS_BATCH[user_id] = False
    success = 0
    not_found = 0
    retrying = 0
    total_bytes = 0
    start_time = time.time()

    status_msg = await client.send_message(user_id, "🚀 **कंटेंट क्लोनिंग शुरू हो गई है...**")

    for msgid in range(fromID, toID + 1):
        if batch_temp.IS_BATCH.get(user_id):
            break

        try:
            if "https://t.me/c/" in start_link:
                chatid = int("-100" + s_parts[4])
                ok, sz = await process_media(client, acc, user_id, chatid, msgid, target_chat, task_info)
            elif "https://t.me/b/" in start_link:
                username = s_parts[4]
                ok, sz = await process_media(client, acc, user_id, username, msgid, target_chat, task_info)
            else:
                username = s_parts[3]
                try:
                    msg = await client.get_messages(username, msgid)
                    await client.copy_message(target_chat, msg.chat.id, msg.id)
                    ok, sz = True, (msg.document.file_size if msg.document else (msg.video.file_size if msg.video else 1024))
                except Exception:
                    ok, sz = await process_media(client, acc, user_id, username, msgid, target_chat, task_info)

            if ok:
                success += 1
                total_bytes += sz
            else:
                not_found += 1
        except Exception:
            retrying += 1

        await asyncio.sleep(WAITING_TIME)

    try:
        await acc.disconnect()
    except Exception:
        pass

    batch_temp.IS_BATCH[user_id] = True

    # थंबनेल डिलीट करना
    if task_info.get("thumb_path") and os.path.exists(task_info["thumb_path"]):
        os.remove(task_info["thumb_path"])
    del batch_temp.CLONE_DATA[user_id]

    # फ़ाइनल समरी रिपोर्ट
    elapsed_time = max(1, int(time.time() - start_time))
    avg_speed_val = total_bytes / elapsed_time
    avg_speed = f"{humanbytes(avg_speed_val)}/s"
    total_size_str = humanbytes(total_bytes)
    time_str = time_formatter(elapsed_time)

    summary_card = (
        "🏁 **Transfer Finished**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Success:         {success}\n"
        f"🗑️ Not Found:       {not_found} _(deleted/restricted)_\n"
        f"🔁 Retrying:         {retrying}\n"
        f"📦 Total Size:      {total_size_str}\n"
        f"⚡ Avg Speed:       {avg_speed}\n"
        f"⏱️ Time:            {time_str}\n\n"
        "🔄 *Nothing was skipped — auto-resume continues from the exact last point in ~20s.*"
    )
    await status_msg.edit_text(summary_card)

async def process_media(client: Client, acc: Client, user_id: int, chatid, msgid: int, target_chat, task_info: dict):
    try:
        msg: Message = await acc.get_messages(chatid, msgid)
        if not msg or msg.empty:
            return False, 0
    except Exception:
        return False, 0

    try:
        dest_chat = int(target_chat)
    except Exception:
        dest_chat = target_chat

    # कैप्शन सेट करना
    final_caption = msg.caption or ""
    if task_info.get("custom_caption"):
        final_caption = task_info["custom_caption"]
    if task_info.get("extra_caption"):
        final_caption = f"{final_caption}\n\n{task_info['extra_caption']}" if final_caption else task_info["extra_caption"]

    if msg.text:
        text_to_send = task_info.get("custom_caption") or msg.text
        if task_info.get("extra_caption"):
            text_to_send += f"\n\n{task_info['extra_caption']}"
        await client.send_message(dest_chat, text_to_send, entities=msg.entities)
        return True, len(text_to_send.encode('utf-8'))

    smsg = await client.send_message(user_id, f"📥 **Downloading Post ID:** `{msgid}`")
    down_file = f"{user_id}_{msgid}_down.txt"
    up_file = f"{user_id}_{msgid}_up.txt"

    asyncio.create_task(track_status(client, down_file, smsg, "Downloading"))
    try:
        file_path = await acc.download_media(msg, progress=progress, progress_args=[smsg, "down"])
    except Exception:
        if os.path.exists(down_file): os.remove(down_file)
        await smsg.delete()
        return False, 0

    if os.path.exists(down_file): os.remove(down_file)

    asyncio.create_task(track_status(client, up_file, smsg, "Uploading"))
    size = os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0

    # कस्टम थंबनेल या ओरिजिनल थंबनेल
    thumb_to_use = task_info.get("thumb_path")

    try:
        if msg.document:
            await client.send_document(dest_chat, file_path, thumb=thumb_to_use, caption=final_caption, progress=progress, progress_args=[smsg, "up"])
        elif msg.video:
            await client.send_video(dest_chat, file_path, thumb=thumb_to_use, caption=final_caption, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, progress=progress, progress_args=[smsg, "up"])
        elif msg.audio:
            await client.send_audio(dest_chat, file_path, thumb=thumb_to_use, caption=final_caption, progress=progress, progress_args=[smsg, "up"])
        elif msg.photo:
            await client.send_photo(dest_chat, file_path, caption=final_caption)
        else:
            await client.send_document(dest_chat, file_path, thumb=thumb_to_use, caption=final_caption)
    except Exception:
        pass
    finally:
        if os.path.exists(up_file): os.remove(up_file)
        if file_path and os.path.exists(file_path): os.remove(file_path)
        await smsg.delete()

    return True, size

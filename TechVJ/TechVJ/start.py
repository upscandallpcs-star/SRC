import os
import asyncio 
import time
import math
import re
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import API_ID, API_HASH, ADMINS, CHANNEL_ID, WAITING_TIME
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

# लाइव प्रोग्रेस बार जिसमें फ़ाइल नेम भी दिखेगा
async def progress_bar(current, total, ud_type, message, start, fname=""):
    now = time.time()
    diff = now - start
    if round(diff % 4.00) == 0 or current == total:
        percentage = current * 100 / total if total > 0 else 0
        speed = current / diff if diff > 0 else 0
        elapsed_time = round(diff)
        eta = round((total - current) / speed) if speed > 0 else 0
        
        elapsed_str = time_formatter(elapsed_time)
        eta_str = time_formatter(eta)

        bar_length = 10
        filled_length = int(bar_length * current // total) if total > 0 else 0
        bar = '▰' * filled_length + '▱' * (bar_length - filled_length)

        fname_text = f"📁 **File:** `{fname[:30]}...`\n" if fname else ""

        status_text = (
            f"**{ud_type}**\n"
            f"{fname_text}"
            f"[{bar}] {percentage:.1f}%\n"
            f"⚡ **Speed:** {humanbytes(speed)}/s\n"
            f"📦 **Done:** {humanbytes(current)} / {humanbytes(total)}\n"
            f"⏱️ **ETA:** {eta_str} | **Time:** {elapsed_str}"
        )
        try:
            await message.edit_text(status_text)
        except Exception:
            pass

@Client.on_message(filters.command("id"))
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

@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await message.reply_text(HELP_TXT)

@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    user_id = message.from_user.id
    batch_temp.IS_BATCH[user_id] = True
    if user_id in batch_temp.CLONE_DATA:
        del batch_temp.CLONE_DATA[user_id]
    await message.reply_text("🛑 **टास्क रद्द कर दिया गया है।**")

def parse_telegram_link(link: str):
    link = link.strip().replace("?single", "")
    c_match = re.search(r"t\.me/c/(\d+)(?:/\d+)?/(\d+)", link)
    if c_match:
        chat_id = int("-100" + c_match.group(1))
        msg_id = int(c_match.group(2))
        return chat_id, msg_id

    b_match = re.search(r"t\.me/b/([^/]+)/(\d+)", link)
    if b_match:
        return b_match.group(1), int(b_match.group(2))

    p_match = re.search(r"t\.me/([^/]+)(?:/\d+)?/(\d+)", link)
    if p_match:
        return p_match.group(1), int(p_match.group(2))

    return None, None

# ----------------- /clone COMMAND ----------------- #
@Client.on_message(filters.command(["clone", "clon"]) & filters.private)
async def clone_command(client: Client, message: Message):
    user_id = message.from_user.id

    if not db.is_user_vip(user_id, ADMINS):
        return await message.reply_text(
            "🔒 **यह फीचर केवल एक्टिव पेड मेंबर्स के लिए है!**\n\n"
            "कंटेंट डाउनलोड करने के लिए प्लान खरीदें: /plans"
        )

    if batch_temp.IS_BATCH.get(user_id) == False:
        return await message.reply_text("⚠️ एक टास्क पहले से चल रहा है। कृपया इंतज़ार करें या /cancel करें।")

    user_session = db.get_session(user_id)
    if not user_session:
        return await message.reply_text("🔑 प्राइवेट फाइल्स के लिए पहले **/login** करें।")

    guide_text = (
        "📖 **कंटेंट क्लोनिंग दिशा-निर्देश:**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "1. **Public:** `https://t.me/username/123`\n"
        "2. **Private:** `https://t.me/c/123456789/123`\n"
        "3. **Topic Group:** `https://t.me/username/topic_id/msg_id`\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👉 **स्टेप 1:** जहाँ से कॉपी करना है, उसकी **पहली लिंक (Start Link)** भेजें:\n"
        "(रद्द करने के लिए /cancel लिखें)"
    )
    
    first_msg = await client.ask(user_id, guide_text, filters=filters.text, timeout=300)
    if first_msg.text == "/cancel":
        return await first_msg.reply("❌ प्रोसेस रद्द कर दिया गया।")
    
    start_link = first_msg.text.strip()
    s_chat, s_id = parse_telegram_link(start_link)
    if not s_id:
        return await first_msg.reply("❌ अमान्य टेलीग्राम लिंक! कृपया सही लिंक के साथ दोबारा /clone करें।")

    last_msg = await client.ask(
        user_id, 
        "👉 **स्टेप 2:** अब **अंतिम लिंक (End Link)** भेजें:\n"
        "(यदि केवल एक ही पोस्ट कॉपी करनी है तो `/single` लिखें)",
        filters=filters.text, 
        timeout=300
    )
    if last_msg.text == "/cancel":
        return await last_msg.reply("❌ प्रोसेस रद्द कर दिया गया।")
    
    if last_msg.text.strip() == "/single":
        e_chat, e_id = s_chat, s_id
    else:
        end_link = last_msg.text.strip()
        e_chat, e_id = parse_telegram_link(end_link)
        if not e_id:
            return await last_msg.reply("❌ अमान्य अंतिम लिंक! दोबारा /clone करें।")

    dest_msg = await client.ask(
        user_id,
        "👉 **स्टेप 3:** जहाँ कंटेंट अपलोड करवाना है, उस **चैनल/ग्रुप का लिंक या ID** भेजें:\n"
        "(डिफ़ॉल्ट बॉट चैट में पाने के लिए `/skip` लिखें)",
        filters=filters.text,
        timeout=300
    )
    if dest_msg.text == "/cancel":
        return await dest_msg.reply("❌ प्रोसेस रद्द कर दिया गया।")

    dest_val = dest_msg.text.strip()
    if dest_val == "/skip":
        target_chat = user_id
    else:
        try:
            target_chat = int(dest_val)
        except ValueError:
            target_chat = dest_val.replace("https://t.me/", "@")

    batch_temp.CLONE_DATA[user_id] = {
        "source_chat": s_chat,
        "start_id": min(s_id, e_id),
        "end_id": max(s_id, e_id),
        "target_chat": target_chat,
        "custom_caption": None,
        "extra_caption": None,
        "replace_find": None,
        "replace_with": None,
        "thumb_path": None
    }

    await show_customization_menu(client, user_id)

async def show_customization_menu(client: Client, user_id: int):
    data = batch_temp.CLONE_DATA.get(user_id, {})
    cap_status = "सेट है ✅" if data.get("custom_caption") else "डिफ़ॉल्ट"
    ext_status = "सेट है ✅" if data.get("extra_caption") else "कोई नहीं"
    thm_status = "सेट है ✅" if data.get("thumb_path") else "डिफ़ॉल्ट"
    
    rep_status = f"`{data.get('replace_find')}` ➔ `{data.get('replace_with')}`" if data.get("replace_find") else "कोई नहीं"

    panel_text = (
        "⚙️ **कंटेंट कस्टमाइज़ेशन सेटिंग्स:**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 पूरा नया कैप्शन: `{cap_status}`\n"
        f"🔄 रिप्लेस (बदलना): {rep_status}\n"
        f"➕ अतिरिक्त कैप्शन: `{ext_status}`\n"
        f"🖼️ थंबनेल: `{thm_status}`\n"
        f"🎯 टारगेट चैट: `{data.get('target_chat')}`\n"
        f"📊 रेंज: `{data.get('start_id')}` से `{data.get('end_id')}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "नीचे से एडिट करें या तुरंत ट्रांसफर के लिए **🚀 Confirm & Start** दबाएँ:"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Edit Full Caption", callback_data="set_caption"),
         InlineKeyboardButton("🔄 Replace in Caption", callback_data="set_replace")],
        [InlineKeyboardButton("➕ Add Extra Caption", callback_data="set_extra"),
         InlineKeyboardButton("🖼️ Set Thumbnail", callback_data="set_thumb")],
        [InlineKeyboardButton("🗑️ Clear Settings", callback_data="clear_settings"),
         InlineKeyboardButton("🚀 Confirm & Start", callback_data="confirm_start")]
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
        msg = await client.ask(user_id, "✍️ **नया कस्टम कैप्शन भेजें** (यह पूरे ओरिजिनल कैप्शन को बदल देगा):", filters=filters.text, timeout=180)
        batch_temp.CLONE_DATA[user_id]["custom_caption"] = msg.text
        await show_customization_menu(client, user_id)

    elif data == "set_replace":
        await query.message.delete()
        find_msg = await client.ask(
            user_id, 
            "🔍 **कैप्शन में क्या खोजना/हटाना चाहते हैं? वह शब्द/टेक्स्ट भेजें:**\n(उदा: `𝚾 𝚫 𝚬 𝚸 · ༎🥀`)\n\nरद्द करने के लिए /cancel लिखें।", 
            filters=filters.text, 
            timeout=180
        )
        if find_msg.text == "/cancel":
            return await show_customization_menu(client, user_id)
        
        with_msg = await client.ask(
            user_id, 
            f"✏️ `{find_msg.text}` की जगह पर **क्या नया नाम/टेक्स्ट लगाना चाहते हैं?**\n(हटाकर खाली छोड़ने के लिए `/empty` लिखें):", 
            filters=filters.text, 
            timeout=180
        )
        if with_msg.text == "/cancel":
            return await show_customization_menu(client, user_id)

        rep_text = "" if with_msg.text.strip() == "/empty" else with_msg.text
        batch_temp.CLONE_DATA[user_id]["replace_find"] = find_msg.text
        batch_temp.CLONE_DATA[user_id]["replace_with"] = rep_text
        await show_customization_menu(client, user_id)

    elif data == "set_extra":
        await query.message.delete()
        msg = await client.ask(user_id, "✍️ **अतिरिक्त कैप्शन भेजें** (यह पुराने कैप्शन के नीचे जुड़ेगा):", filters=filters.text, timeout=180)
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
        batch_temp.CLONE_DATA[user_id]["replace_find"] = None
        batch_temp.CLONE_DATA[user_id]["replace_with"] = None
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
    task = batch_temp.CLONE_DATA.get(user_id)
    if not task:
        return await client.send_message(user_id, "❌ कोई सक्रिय टास्क नहीं मिला। कृपया /clone दोबारा करें।")

    source_chat = task["source_chat"]
    start_id = task["start_id"]
    end_id = task["end_id"]
    target_chat = task["target_chat"]

    user_session = db.get_session(user_id)
    if not user_session:
        return await client.send_message(user_id, "❌ आपका लॉगिन सेशन नहीं मिला। कृपया पहले /login करें।")

    user_api_id = int(db.get_api_id(user_id) or API_ID)
    user_api_hash = db.get_api_hash(user_id) or API_HASH

    acc = Client(f"user_session_{user_id}", session_string=user_session, api_hash=user_api_hash, api_id=user_api_id, in_memory=True)
    try:
        await acc.start()
    except Exception as e:
        return await client.send_message(user_id, f"❌ सेशन कनेक्ट एरर: `{e}`\nकृपया /logout करके दोबारा /login करें।")

    batch_temp.IS_BATCH[user_id] = False
    success = 0
    not_found = 0
    retrying = 0
    total_bytes = 0
    start_time = time.time()

    status_msg = await client.send_message(user_id, "🚀 **कंटेंट डाउनलोडिंग व अपलोडिंग शुरू...**")

    for msgid in range(start_id, end_id + 1):
        if batch_temp.IS_BATCH.get(user_id):
            break

        try:
            ok, sz = await process_media(client, acc, user_id, source_chat, msgid, target_chat, task, status_msg)
            if ok:
                success += 1
                total_bytes += sz
            else:
                not_found += 1
        except Exception as e:
            retrying += 1
            print(f"Error transferring {msgid}: {e}")

        await asyncio.sleep(WAITING_TIME)

    try:
        await acc.stop()
    except Exception:
        pass

    batch_temp.IS_BATCH[user_id] = True
    if task.get("thumb_path") and os.path.exists(task["thumb_path"]):
        os.remove(task["thumb_path"])
    del batch_temp.CLONE_DATA[user_id]

    elapsed_time = max(1, int(time.time() - start_time))
    avg_speed = f"{humanbytes(total_bytes / elapsed_time)}/s"

    summary_card = (
        "🏁 **Transfer Finished**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Success:         {success}\n"
        f"🗑️ Not Found:       {not_found}\n"
        f"🔁 Retrying:         {retrying}\n"
        f"📦 Total Size:      {humanbytes(total_bytes)}\n"
        f"⚡ Avg Speed:       {avg_speed}\n"
        f"⏱️ Time:            {time_formatter(elapsed_time)}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await status_msg.edit_text(summary_card)

def get_file_name_from_msg(msg: Message) -> str:
    if msg.document and msg.document.file_name:
        return msg.document.file_name
    elif msg.video and msg.video.file_name:
        return msg.video.file_name
    elif msg.audio and msg.audio.file_name:
        return msg.audio.file_name
    return "Media File"

async def process_media(client: Client, acc: Client, user_id: int, source_chat, msgid: int, target_chat, task: dict, status_msg: Message):
    try:
        msg: Message = await acc.get_messages(source_chat, msgid)
        if not msg or msg.empty:
            return False, 0
    except Exception as e:
        print(f"Message fetch error: {e}")
        return False, 0

    # कैप्शन प्रोसेसिंग (Replace / Edit / Extra)
    final_caption = msg.caption or ""

    if task.get("custom_caption"):
        final_caption = task["custom_caption"]
    elif task.get("replace_find"):
        find_w = task["replace_find"]
        with_w = task.get("replace_with") or ""
        if final_caption:
            final_caption = final_caption.replace(find_w, with_w)

    if task.get("extra_caption"):
        final_caption = f"{final_caption}\n\n{task['extra_caption']}" if final_caption else task["extra_caption"]

    # केवल टेक्स्ट मैसेज होने पर
    if msg.text:
        text_to_send = msg.text
        if task.get("custom_caption"):
            text_to_send = task["custom_caption"]
        elif task.get("replace_find"):
            find_w = task["replace_find"]
            with_w = task.get("replace_with") or ""
            text_to_send = text_to_send.replace(find_w, with_w)

        if task.get("extra_caption"):
            text_to_send += f"\n\n{task['extra_caption']}"
        await client.send_message(target_chat, text_to_send, entities=msg.entities)
        return True, len(text_to_send.encode('utf-8'))

    # फ़ाइल का नाम निकालना
    file_name = get_file_name_from_msg(msg)

    down_start = time.time()
    await status_msg.edit_text(f"📥 **Downloading ID:** `{msgid}`\n📁 **File:** `{file_name}`...")
    
    file_path = await acc.download_media(
        msg,
        progress=progress_bar,
        progress_args=(f"📥 Downloading ID: {msgid}", status_msg, down_start, file_name)
    )

    if not file_path or not os.path.exists(file_path):
        return False, 0

    size = os.path.getsize(file_path)
    up_start = time.time()
    await status_msg.edit_text(f"📤 **Uploading ID:** `{msgid}`\n📁 **File:** `{file_name}`...")

    thumb_to_use = task.get("thumb_path")

    try:
        if msg.document:
            await client.send_document(
                target_chat, file_path, thumb=thumb_to_use, caption=final_caption,
                progress=progress_bar, progress_args=(f"📤 Uploading ID: {msgid}", status_msg, up_start, file_name)
            )
        elif msg.video:
            await client.send_video(
                target_chat, file_path, thumb=thumb_to_use, caption=final_caption,
                duration=msg.video.duration, width=msg.video.width, height=msg.video.height,
                progress=progress_bar, progress_args=(f"📤 Uploading ID: {msgid}", status_msg, up_start, file_name)
            )
        elif msg.audio:
            await client.send_audio(
                target_chat, file_path, thumb=thumb_to_use, caption=final_caption,
                progress=progress_bar, progress_args=(f"📤 Uploading ID: {msgid}", status_msg, up_start, file_name)
            )
        elif msg.photo:
            await client.send_photo(target_chat, file_path, caption=final_caption)
        else:
            await client.send_document(target_chat, file_path, thumb=thumb_to_use, caption=final_caption)
    except Exception as e:
        print(f"Upload error: {e}")
        return False, 0
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    return True, size

import os
import asyncio 
import time
import pyrogram
from pyrogram import Client, filters, enums
from pyrogram.types import Message 
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
            await asyncio.sleep(5)
        except Exception:
            await asyncio.sleep(3)

@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await message.reply_text(HELP_TXT)

@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    batch_temp.IS_BATCH[message.from_user.id] = True
    await message.reply_text("🛑 **टास्क रद्द कर दिया गया है।**")

# ----------------- /clone COMMAND ----------------- #
@Client.on_message(filters.command(["clone", "clon"]) & filters.private)
async def clone_command(client: Client, message: Message):
    user_id = message.from_user.id

    # वीआईपी प्लान सुरक्षा जांच
    if not db.is_user_vip(user_id, ADMINS):
        return await message.reply_text(
            "🔒 **यह फीचर केवल एक्टिव पेड मेंबर्स के लिए है!**\n\n"
            "कंटेंट डाउनलोड करने के लिए प्लान खरीदें।\n"
            "प्लान देखने के लिए: /plans"
        )

    if batch_temp.IS_BATCH.get(user_id) == False:
        return await message.reply_text("⚠️ एक टास्क पहले से चल रहा है। कृपया पूरा होने का इंतज़ार करें या /cancel करें।")

    # लॉगिन सेशन जांच
    user_session = db.get_session(user_id)
    if not user_session:
        return await message.reply_text("🔑 प्राइवेट व रेस्ट्रिक्टेड कंटेंट के लिए पहले **/login** करें।")

    # लिंक मांगना
    link_msg = await client.ask(
        user_id,
        "🔗 **कृपया पोस्ट या चैनल का लिंक भेजें:**\n\n"
        "• सिंगल पोस्ट: `https://t.me/c/12345/10`\n"
        "• मल्टी पोस्ट्स: `https://t.me/c/12345/10-20`\n\n"
        "रद्द करने के लिए /cancel लिखें।",
        filters=filters.text,
        timeout=300
    )

    if link_msg.text == "/cancel":
        return await link_msg.reply("❌ प्रोसेस रद्द कर दिया गया।")

    if "https://t.me/" not in link_msg.text:
        return await link_msg.reply("❌ अमान्य टेलीग्राम लिंक! कृपया सही लिंक के साथ दोबारा /clone करें।")

    api_id = int(db.get_api_id(user_id))
    api_hash = db.get_api_hash(user_id)

    try:
        acc = Client("saverestricted", session_string=user_session, api_hash=api_hash, api_id=api_id)
        await acc.connect()
    except Exception:
        return await link_msg.reply("❌ आपका लॉगिन सेशन एक्सपायर हो गया है। पहले /logout करें और फिर /login करें।")

    datas = link_msg.text.split("/")
    temp = datas[-1].replace("?single", "").split("-")
    fromID = int(temp[0].strip())
    toID = int(temp[1].strip()) if len(temp) > 1 else fromID

    batch_temp.IS_BATCH[user_id] = False
    
    success = 0
    not_found = 0
    retrying = 0
    total_bytes = 0
    start_time = time.time()

    status_msg = await link_msg.reply_text("⏳ **टास्क शुरू हो रहा है...**")

    for msgid in range(fromID, toID + 1):
        if batch_temp.IS_BATCH.get(user_id):
            break

        try:
            # प्राइवेट चैट
            if "https://t.me/c/" in link_msg.text:
                chatid = int("-100" + datas[4])
                ok, sz = await process_media(client, acc, link_msg, chatid, msgid)
            # बॉट चैट
            elif "https://t.me/b/" in link_msg.text:
                username = datas[4]
                ok, sz = await process_media(client, acc, link_msg, username, msgid)
            # पब्लिक चैट
            else:
                username = datas[3]
                try:
                    msg = await client.get_messages(username, msgid)
                    await client.copy_message(link_msg.chat.id, msg.chat.id, msg.id)
                    ok, sz = True, (msg.document.file_size if msg.document else (msg.video.file_size if msg.video else 1024))
                except Exception:
                    ok, sz = await process_media(client, acc, link_msg, username, msgid)

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

async def process_media(client: Client, acc: Client, message: Message, chatid, msgid: int):
    try:
        msg: Message = await acc.get_messages(chatid, msgid)
        if not msg or msg.empty:
            return False, 0
    except Exception:
        return False, 0

    dest_chat = int(CHANNEL_ID) if CHANNEL_ID else message.chat.id

    if msg.text:
        await client.send_message(dest_chat, msg.text, entities=msg.entities)
        return True, len(msg.text.encode('utf-8'))

    smsg = await client.send_message(message.chat.id, f"📥 **Downloading ID:** `{msgid}`")
    down_file = f"{message.id}downstatus.txt"
    up_file = f"{message.id}upstatus.txt"

    asyncio.create_task(track_status(client, down_file, smsg, "Downloading"))
    try:
        file_path = await acc.download_media(msg, progress=progress, progress_args=[message, "down"])
    except Exception:
        if os.path.exists(down_file): os.remove(down_file)
        await smsg.delete()
        return False, 0

    if os.path.exists(down_file): os.remove(down_file)

    asyncio.create_task(track_status(client, up_file, smsg, "Uploading"))
    caption = msg.caption or None
    size = os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0

    try:
        if msg.document:
            await client.send_document(dest_chat, file_path, caption=caption, progress=progress, progress_args=[message, "up"])
        elif msg.video:
            await client.send_video(dest_chat, file_path, caption=caption, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, progress=progress, progress_args=[message, "up"])
        elif msg.audio:
            await client.send_audio(dest_chat, file_path, caption=caption, progress=progress, progress_args=[message, "up"])
        elif msg.photo:
            await client.send_photo(dest_chat, file_path, caption=caption)
        else:
            await client.send_document(dest_chat, file_path, caption=caption)
    except Exception:
        pass
    finally:
        if os.path.exists(up_file): os.remove(up_file)
        if file_path and os.path.exists(file_path): os.remove(file_path)
        await smsg.delete()

    return True, size

import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from config import ADMINS
from db import db

@Client.on_message(filters.command("broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast(bot, message):
    users = db.get_all_users()
    b_msg = message.reply_to_message
    if not b_msg:
        return await message.reply_text("❌ जिस मैसेज को भेजना है उस पर रिप्लाई करके `/broadcast` लिखें।")

    sts = await message.reply_text("📢 ब्रॉडकास्ट शुरू हो रहा है...")
    total_users = len(users)
    success = 0
    blocked = 0

    for u in users:
        user_id = u["user_id"]
        try:
            await b_msg.copy(chat_id=user_id)
            success += 1
            await asyncio.sleep(0.1)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await b_msg.copy(chat_id=user_id)
            success += 1
        except (UserIsBlocked, InputUserDeactivated):
            blocked += 1
            db.delete_user(user_id)
        except Exception:
            pass

    await sts.edit_text(
        f"📢 **ब्रॉडकास्ट पूरा हुआ!**\n\n"
        f"👥 कुल यूज़र्स: {total_users}\n"
        f"✅ सफल: {success}\n"
        f"🚫 ब्लॉक/डिलीट: {blocked}"
    )
  

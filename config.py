import os

# Telegram Bot Credentials
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")

# Admin ID
ADMINS = int(os.environ.get("ADMINS", "0"))

# Supabase Credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://ejidpxqnfyxapbywhkmd.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Channel to upload files (optional)
CHANNEL_ID = os.environ.get("CHANNEL_ID", "")

# Support & Contact Details
OWNER_HANDLE = "@Avigat1210"
SUPPORT_GROUP = "https://t.me/+oyWBIZplkbAyYTc1"

# Floodwait & Spam protection (in seconds)
WAITING_TIME = int(os.environ.get("WAITING_TIME", "3"))

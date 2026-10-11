from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

class SupabaseDatabase:
    def __init__(self, url: str, key: str):
        self.supabase: Client = create_client(url, key)

    # 1. User Management
    def is_user_exist(self, user_id: int) -> bool:
        res = self.supabase.table("users").select("user_id").eq("user_id", user_id).execute()
        return len(res.data) > 0

    def add_user(self, user_id: int, name: str):
        if not self.is_user_exist(user_id):
            self.supabase.table("users").insert({
                "user_id": user_id,
                "name": name,
                "plan_type": "NONE",
                "plan_expiry": None
            }).execute()

    def get_user(self, user_id: int):
        res = self.supabase.table("users").select("*").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]
        return None

    # 2. String Session Management
    def set_session(self, user_id: int, session: str):
        self.supabase.table("users").update({"session": session}).eq("user_id", user_id).execute()

    def get_session(self, user_id: int):
        res = self.supabase.table("users").select("session").eq("user_id", user_id).execute()
        if res.data and res.data[0].get("session"):
            return res.data[0]["session"]
        return None

    def remove_session(self, user_id: int):
        self.supabase.table("users").update({"session": None}).eq("user_id", user_id).execute()

    # 3. Dynamic Plan Settings (Price & Days)
    def set_plan_config(self, price: str, days: str):
        self.supabase.table("bot_settings").upsert({"setting_key": "plan_price", "setting_value": str(price)}).execute()
        self.supabase.table("bot_settings").upsert({"setting_key": "plan_days", "setting_value": str(days)}).execute()

    def get_plan_config(self):
        res = self.supabase.table("bot_settings").select("*").execute()
        config = {"plan_price": "150", "plan_days": "15"}
        for item in res.data:
            if item["setting_key"] == "plan_price":
                config["plan_price"] = item["setting_value"]
            elif item["setting_key"] == "plan_days":
                config["plan_days"] = item["setting_value"]
        return config

    # 4. Paid Subscription Checks
    def is_user_vip(self, user_id: int, admin_id: int) -> bool:
        if user_id == admin_id:
            return True
        user = self.get_user(user_id)
        if not user or not user.get("plan_expiry"):
            return False
        expiry = datetime.fromisoformat(user["plan_expiry"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return now < expiry

    def add_vip_user(self, user_id: int, days: int):
        expiry_date = datetime.now(timezone.utc) + timedelta(days=days)
        self.supabase.table("users").upsert({
            "user_id": user_id,
            "plan_type": "PAID",
            "plan_expiry": expiry_date.isoformat()
        }).execute()

    def remove_vip_user(self, user_id: int):
        self.supabase.table("users").update({
            "plan_type": "NONE",
            "plan_expiry": None
        }).execute().eq("user_id", user_id)

    # 5. Broadcast & Stats
    def get_all_users(self):
        res = self.supabase.table("users").select("user_id").execute()
        return res.data

db = SupabaseDatabase(SUPABASE_URL, SUPABASE_KEY)

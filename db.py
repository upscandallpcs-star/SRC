from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

class SupabaseDatabase:
    def __init__(self, url: str, key: str):
        self.supabase: Client = create_client(url, key)

    def is_user_exist(self, user_id: int) -> bool:
        try:
            res = self.supabase.table("users").select("user_id").eq("user_id", int(user_id)).execute()
            return len(res.data) > 0
        except Exception:
            return False

    def add_user(self, user_id: int, name: str):
        try:
            if not self.is_user_exist(user_id):
                self.supabase.table("users").insert({
                    "user_id": int(user_id),
                    "name": name,
                    "plan_type": "NONE",
                    "plan_expiry": None
                }).execute()
        except Exception:
            pass

    def get_user(self, user_id: int):
        try:
            res = self.supabase.table("users").select("*").eq("user_id", int(user_id)).execute()
            return res.data[0] if res.data else None
        except Exception:
            return None

    def set_session(self, user_id: int, session: str):
        try:
            self.supabase.table("users").update({"session": session}).eq("user_id", int(user_id)).execute()
        except Exception:
            pass

    def get_session(self, user_id: int):
        user = self.get_user(user_id)
        return user.get("session") if user else None

    def remove_session(self, user_id: int):
        try:
            self.supabase.table("users").update({"session": None}).eq("user_id", int(user_id)).execute()
        except Exception:
            pass

    def set_api_id(self, user_id: int, api_id: str):
        try:
            self.supabase.table("users").update({"api_id": str(api_id)}).eq("user_id", int(user_id)).execute()
        except Exception:
            pass

    def get_api_id(self, user_id: int):
        user = self.get_user(user_id)
        return user.get("api_id") if user else None

    def set_api_hash(self, user_id: int, api_hash: str):
        try:
            self.supabase.table("users").update({"api_hash": str(api_hash)}).eq("user_id", int(user_id)).execute()
        except Exception:
            pass

    def get_api_hash(self, user_id: int):
        user = self.get_user(user_id)
        return user.get("api_hash") if user else None

    def delete_user(self, user_id: int):
        try:
            self.supabase.table("users").delete().eq("user_id", int(user_id)).execute()
        except Exception:
            pass

    def set_plan_config(self, price: str, days: str):
        try:
            self.supabase.table("bot_settings").upsert({"setting_key": "plan_price", "setting_value": str(price)}).execute()
            self.supabase.table("bot_settings").upsert({"setting_key": "plan_days", "setting_value": str(days)}).execute()
        except Exception:
            pass

    def get_plan_config(self):
        try:
            res = self.supabase.table("bot_settings").select("*").execute()
            config = {"plan_price": "150", "plan_days": "15"}
            for item in res.data:
                if item["setting_key"] == "plan_price":
                    config["plan_price"] = item["setting_value"]
                elif item["setting_key"] == "plan_days":
                    config["plan_days"] = item["setting_value"]
            return config
        except Exception:
            return {"plan_price": "150", "plan_days": "15"}

    def is_user_vip(self, user_id: int, admin_id: int) -> bool:
        if int(user_id) == int(admin_id):
            return True
        user = self.get_user(user_id)
        if not user or not user.get("plan_expiry"):
            return False
        try:
            expiry = datetime.fromisoformat(user["plan_expiry"].replace("Z", "+00:00"))
            return datetime.now(timezone.utc) < expiry
        except Exception:
            return False

    def add_vip_user(self, user_id: int, days: int):
        try:
            expiry_date = datetime.now(timezone.utc) + timedelta(days=days)
            self.supabase.table("users").upsert({
                "user_id": int(user_id),
                "plan_type": "PAID",
                "plan_expiry": expiry_date.isoformat()
            }).execute()
        except Exception:
            pass

    def remove_vip_user(self, user_id: int):
        try:
            self.supabase.table("users").update({"plan_type": "NONE", "plan_expiry": None}).eq("user_id", int(user_id)).execute()
        except Exception:
            pass

    def get_all_users(self):
        try:
            res = self.supabase.table("users").select("user_id").execute()
            return res.data
        except Exception:
            return []

db = SupabaseDatabase(SUPABASE_URL, SUPABASE_KEY)

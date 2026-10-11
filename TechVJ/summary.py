def get_transfer_summary(success: int, not_found: int, retrying: int, total_size_str: str, avg_speed_str: str, time_taken_str: str) -> str:
    return (
        "🏁 **Transfer Finished**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Success:         {success}\n"
        f"🗑️ Not Found:       {not_found} _(deleted/restricted)_\n"
        f"🔁 Retrying:         {retrying}\n"
        f"📦 Total Size:      {total_size_str}\n"
        f"⚡ Avg Speed:       {avg_speed_str}\n"
        f"⏱️ Time:            {time_taken_str}\n\n"
        "🔄 *Nothing was skipped — auto-resume continues from the exact last point in ~20s.*"
    )
  

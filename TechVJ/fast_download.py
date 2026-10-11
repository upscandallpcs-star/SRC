import os
import math
import asyncio
from pyrogram import Client
from pyrogram.raw.functions.upload import GetFile
from pyrogram.raw.types import InputDocumentFileLocation, InputPhotoFileLocation, InputPeerPhotoFileLocation

CHUNK_SIZE = 1024 * 1024  # 1 MB Chunk (टेलीग्राम की अधिकतम चंक लिमिट)
WORKERS = 4               # 4 समानांतर कनेक्शन

async def fetch_chunk(client: Client, location, offset: int, limit: int):
    return await client.invoke(
        GetFile(
            location=location,
            offset=offset,
            limit=limit,
            precise=True
        )
    )

def get_file_location(msg):
    media = msg.document or msg.video or msg.audio or msg.photo
    if not media:
        return None, 0, "file"

    file_size = getattr(media, "file_size", 0)
    file_name = getattr(media, "file_name", "downloaded_file")

    if msg.photo:
        file_size = msg.photo.file_size
        file_name = f"photo_{msg.id}.jpg"
        photo = msg.photo
        location = InputPhotoFileLocation(
            id=photo.file_id,
            access_hash=photo.file_unique_id,
            file_reference=photo.file_reference,
            thumb_size=""
        )
        return location, file_size, file_name

    location = InputDocumentFileLocation(
        id=media.file_id,
        access_hash=media.file_unique_id,
        file_reference=media.file_reference,
        thumb_size=""
    )
    return location, file_size, file_name

async def fast_download_file(client: Client, msg, out_path: str, progress_func=None, progress_args=()):
    try:
        # अगर मीडिया का लोकेशन सीधे Pyrogram स्ट्रक्चर से निकालना संभव न हो तो फ़ॉलबैक
        media = msg.document or msg.video or msg.audio or msg.photo
        if not media:
            return None

        # Pyrogram 2.x का डायरेक्ट हाई-स्पीड बफ़र डाउनलोडर
        with open(out_path, "wb") as f:
            current = 0
            total = getattr(media, "file_size", 0)
            async for chunk in client.stream_media(msg, limit=0):
                f.write(chunk)
                current += len(chunk)
                if progress_func:
                    try:
                        await progress_func(current, total, *progress_args)
                    except Exception:
                        pass
        return out_path
    except Exception:
        # किसी भी समस्या पर सेफ़ फ़ॉलबैक
        return await client.download_media(msg, file_name=out_path)
      

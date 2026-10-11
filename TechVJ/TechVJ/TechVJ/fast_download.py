import os
import math
import asyncio
import time
from pyrogram import Client
from pyrogram.raw.functions.upload import GetFile
from pyrogram.raw.types import InputDocumentFileLocation, InputPhotoFileLocation

# 1024 KB (1 MB) चंक साइज़
CHUNK_SIZE = 1024 * 1024
# 8 समानांतर पैरेलल वर्कर्स (यह टेलीग्राम की 260 KB/s थ्रॉटलिंग को बाईपास करता है)
PARALLEL_WORKERS = 8

async def download_chunk_part(client: Client, location, offset: int, limit: int):
    retries = 3
    while retries > 0:
        try:
            res = await client.invoke(
                GetFile(
                    location=location,
                    offset=offset,
                    limit=limit,
                    precise=True
                )
            )
            return res.bytes
        except Exception:
            retries -= 1
            await asyncio.sleep(0.5)
    return b""

async def fast_download_file(client: Client, msg, out_path: str, progress_func=None, progress_args=()):
    media = msg.document or msg.video or msg.audio or msg.photo
    if not media:
        return None

    file_size = getattr(media, "file_size", 0)
    if not file_size or file_size < 10 * 1024 * 1024:
        # 10 MB से छोटी फाइलों को डिफ़ॉल्ट रूप से तुरंत डाउनलोड करें
        return await client.download_media(msg, file_name=out_path)

    # लोकेशन एक्सट्रेक्ट करना
    if msg.photo:
        photo = msg.photo
        location = InputPhotoFileLocation(
            id=photo.file_id,
            access_hash=photo.file_unique_id,
            file_reference=photo.file_reference,
            thumb_size=""
        )
    else:
        location = InputDocumentFileLocation(
            id=media.file_id,
            access_hash=media.file_unique_id,
            file_reference=media.file_reference,
            thumb_size=""
        )

    total_chunks = math.ceil(file_size / CHUNK_SIZE)
    chunks_dict = {}
    downloaded_bytes = 0
    start_time = time.time()

    queue = asyncio.Queue()
    for i in range(total_chunks):
        queue.put_nowait(i)

    async def worker():
        nonlocal downloaded_bytes
        while not queue.empty():
            part_id = await queue.get()
            offset = part_id * CHUNK_SIZE
            limit = min(CHUNK_SIZE, file_size - offset)
            
            chunk_data = await download_chunk_part(client, location, offset, limit)
            chunks_dict[part_id] = chunk_data
            downloaded_bytes += len(chunk_data)

            if progress_func:
                try:
                    await progress_func(downloaded_bytes, file_size, *progress_args)
                except Exception:
                    pass
            queue.task_done()

    # 8 समानांतर TCP कनेक्शन्स चालू करें
    workers = [asyncio.create_task(worker()) for _ in range(PARALLEL_WORKERS)]
    await asyncio.gather(*workers)

    # फ़ाइल को सीधे राइट करना
    with open(out_path, "wb") as f:
        for i in range(total_chunks):
            if i in chunks_dict:
                f.write(chunks_dict[i])
            else:
                return None

    chunks_dict.clear()
    return out_path

import os
import math
import asyncio
from pyrogram import Client
from pyrogram.raw.functions.upload import GetFile
from pyrogram.raw.types import InputDocumentFileLocation, InputPhotoFileLocation

CHUNK_SIZE = 1024 * 1024  # 1 MB चंक

async def download_part(client: Client, location, offset: int, limit: int):
    try:
        r = await client.invoke(
            GetFile(
                location=location,
                offset=offset,
                limit=limit,
                precise=True
            )
        )
        return r.bytes
    except Exception:
        return b""

async def fast_download_file(client: Client, msg, out_path: str, progress_func=None, progress_args=()):
    media = msg.document or msg.video or msg.audio or msg.photo
    if not media:
        return None

    file_size = getattr(media, "file_size", 0)
    if not file_size or file_size < 5 * 1024 * 1024:
        # 5 MB से छोटी फाइलों के लिए सामान्य डाउनलोड
        return await client.download_media(msg, file_name=out_path)

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

    part_count = math.ceil(file_size / CHUNK_SIZE)
    downloaded_bytes = 0

    with open(out_path, "wb") as f:
        # 4 पैरेलल चंक्स एक साथ टेलीग्राम सर्वर से खींचना
        semaphore = asyncio.Semaphore(4)

        async def worker(index):
            nonlocal downloaded_bytes
            offset = index * CHUNK_SIZE
            limit = min(CHUNK_SIZE, file_size - offset)
            async with semaphore:
                chunk = await download_part(client, location, offset, limit)
                return index, chunk

        tasks = [worker(i) for i in range(part_count)]
        
        # बैच प्रोसेस ताकि RAM न भरे और स्पीड 4 गुना मिले
        batch_size = 8
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            results = await asyncio.gather(*batch)
            for _, chunk_data in results:
                f.write(chunk_data)
                downloaded_bytes += len(chunk_data)

            if progress_func:
                try:
                    await progress_func(downloaded_bytes, file_size, *progress_args)
                except Exception:
                    pass

    return out_path

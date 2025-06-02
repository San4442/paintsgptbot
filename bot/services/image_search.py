import aiohttp
import logging
import xml.etree.ElementTree as ET
from config import YANDEX_FOLDER_ID, YANDEX_GPT_API_KEY

async def search_images(query: str, n: int = 5) -> list[str]:
    base_url = "https://yandex.ru/images-xml"
    params = {
        "folderid": YANDEX_FOLDER_ID,
        "apikey": YANDEX_GPT_API_KEY,
        "text": f"{query} картина живопись -фото -коллаж -рисунок -скульптура",
        "groupby": f"attr=ii.groups-on-page={n}",
        "p": 0,
        "isize": "large",
        "itype": "jpg"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                response.raise_for_status()
                root = ET.fromstring(await response.text())
                return [
                    link.text for link in root.findall('.//doc//image-link') if link is not None and link.text
                ][:5]
    except Exception as e:
        logging.error(f"Image search failed: {e}")
        return []

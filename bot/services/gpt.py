import aiohttp
import json
import logging
from config import YANDEX_FOLDER_ID, YANDEX_GPT_API_KEY

async def analyze_with_gpt(prompt: str) -> dict | None:
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {YANDEX_GPT_API_KEY}",
        "x-folder-id": YANDEX_FOLDER_ID,
        "Content-Type": "application/json"
    }

    system_prompt = """
Ты — эксперт по искусству. Твоя задача — интерпретировать даже самые краткие, неполные или неточные описания, как возможные описания художественных картин. Если есть шанс, что пользователь имел в виду картину, анализируй это как описание картины.

1. Даже если в запросе только одно слово (например, "звезды", "сад", "Пикассо") — попробуй догадаться, о какой картине может идти речь.
2. Отвечай всегда в формате JSON:
{
  "is_painting": boolean,
  "details": {
    "название": string,
    "автор": string,
    "стиль": string,
    "ключевые_элементы": list[string]
  }
}
3. Если точно не известно название, автор или стиль — пиши "неизвестно".
4. Ключевые элементы должны содержать как можно больше догадок по сюжету, объектам, стилю.
"""

    payload = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt",
        "completionOptions": {
            "stream": False,
            "temperature": 0.4,
            "maxTokens": 1000
        },
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": prompt}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                raw_text = data['result']['alternatives'][0]['message']['text']
                cleaned = raw_text.strip("` \n")
                return json.loads(cleaned)
    except json.JSONDecodeError:
        logging.error(f"Ошибка разбора JSON от GPT: {raw_text}")
        return None
    except Exception as e:
        logging.error(f"GPT Error: {e}", exc_info=True)
        return None

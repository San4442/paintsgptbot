from yandex_search_api import YandexSearchAPIClient
from yandex_search_api.client import SearchType
from config import YANDEX_FOLDER_ID, YANDEX_OAUTH_TOKEN

client = YandexSearchAPIClient(
    folder_id=YANDEX_FOLDER_ID,
    oauth_token=YANDEX_OAUTH_TOKEN
)

def get_links(query: str, n: int = 5) -> list[dict]:
    urls = client.get_links(query_text=query, search_type=SearchType.RUSSIAN, n_links=n)
    results = []
    for url in urls:
        title = url.split("/")[2] if url.startswith("http") else "Источник"
        results.append({"url": url, "title": title})
    return results

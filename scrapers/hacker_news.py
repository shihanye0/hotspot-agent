import asyncio
import httpx

AI_KEYWORDS = [
    "ai", "llm", "gpt", "agent", "rag", "openai", "claude", "deepseek",
    "langchain", "transformer", "diffusion", "embedding", "vector",
    "fine-tune", "lora", "prompt", "token", "inference", "gpu",
]


async def fetch_hacker_news(max_items: int = 10) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        top_resp = await client.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json"
        )
        top_resp.raise_for_status()
        top_ids = top_resp.json()[:30]

    sem = asyncio.Semaphore(10)

    async def fetch_one(item_id):
        async with sem:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(
                        f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
                    )
                    return resp.json()
            except Exception:
                return None

    results = await asyncio.gather(*[fetch_one(i) for i in top_ids])

    items = []
    for item in results:
        if not item:
            continue
        title = item.get("title", "")
        if _is_ai_related(title):
            url = item.get("url") or f"https://news.ycombinator.com/item?id={item.get('id', '')}"
            items.append({
                "id": f"hn:{item.get('id', '')}",
                "title": title,
                "url": url,
                "score": item.get("score", 0),
                "source": "hackernews",
            })
            if len(items) >= max_items:
                break

    return items


def _is_ai_related(title: str) -> bool:
    tl = title.lower()
    return any(kw in tl for kw in AI_KEYWORDS)

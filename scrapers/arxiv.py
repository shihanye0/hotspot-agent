import asyncio
import httpx
import xml.etree.ElementTree as ET


async def fetch_arxiv_papers(
    query: str = "cs.AI", max_results: int = 10
) -> list[dict]:
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"cat:{query}",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": str(max_results),
    }

    resp = None
    for attempt in range(3):
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 429:
                await asyncio.sleep(5 * (attempt + 1))
                continue
            resp.raise_for_status()
            break

    if resp is None or resp.status_code != 200:
        return []

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
    }
    root = ET.fromstring(resp.text)
    items = []

    for entry in root.findall("atom:entry", ns):
        aid = ""
        for id_el in entry.findall("atom:id", ns):
            aid = id_el.text or ""
            break

        arxiv_id = aid.split("/abs/")[-1] if "/abs/" in aid else aid

        title = ""
        for t in entry.findall("atom:title", ns):
            title = (t.text or "").strip().replace("\n", " ")
            break

        summary = ""
        for s in entry.findall("atom:summary", ns):
            summary = (s.text or "").strip()[:300]
            break

        published = ""
        for p in entry.findall("atom:published", ns):
            published = (p.text or "")[:10]
            break

        items.append({
            "id": f"arxiv:{arxiv_id}",
            "title": title,
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "summary": summary,
            "published": published,
            "source": "arxiv",
        })

    return items

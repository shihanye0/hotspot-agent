from datetime import datetime, timedelta
import httpx
from bs4 import BeautifulSoup


async def fetch_github_trending(language: str = "", since: str = "daily") -> list[dict]:
    """抓取 GitHub 热门仓库。优先使用 Trending 页面，失败时回退到 Search API。"""
    try:
        return await _fetch_trending_page(language, since)
    except Exception:
        return await _fetch_via_search_api(language)


async def _fetch_trending_page(language: str, since: str) -> list[dict]:
    url = "https://github.com/trending"
    params = {}
    if language:
        params["language"] = language
    if since and since != "daily":
        params["since"] = since

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []

    for article in soup.select("article.Box-row"):
        h2 = article.select_one("h2 a")
        if not h2:
            continue

        href = h2.get("href", "").strip()
        full_name = href.strip("/")
        parts = full_name.split("/")
        if len(parts) < 2:
            continue

        owner, name = parts[0], parts[1]

        desc_el = article.select_one("p")
        description = desc_el.get_text(strip=True) if desc_el else ""

        stars = ""
        lang = ""
        extras = article.select("div.f6 a, span.d-inline-block")
        for el in extras:
            text = el.get_text(strip=True)
            if any(c.isdigit() for c in text):
                if "star" not in text.lower() and stars == "":
                    stars = text.replace(",", "")
            elif text and not text.startswith("Built") and lang == "":
                lang = text

        items.append({
            "id": f"github:{full_name}",
            "name": full_name,
            "owner": owner,
            "repo_name": name,
            "url": f"https://github.com/{full_name}",
            "description": description,
            "stars_today": stars,
            "language": lang,
            "source": "github",
        })

    return items[:10]


async def _fetch_via_search_api(language: str = "") -> list[dict]:
    since_date = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d")
    q = f"created:>={since_date}"
    if language:
        q += f"+language:{language}"

    url = "https://api.github.com/search/repositories"
    params = {"q": q, "sort": "stars", "order": "desc", "per_page": 10}

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            url,
            params=params,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "hotspot-agent",
            },
        )
        resp.raise_for_status()

    data = resp.json()
    items = []

    for repo in data.get("items", []):
        full_name = repo.get("full_name", "")
        items.append({
            "id": f"github:{full_name}",
            "name": full_name,
            "owner": repo.get("owner", {}).get("login", ""),
            "repo_name": repo.get("name", ""),
            "url": repo.get("html_url", ""),
            "description": repo.get("description") or "",
            "stars_today": str(repo.get("stargazers_count", "")),
            "language": repo.get("language") or "",
            "source": "github",
        })

    return items

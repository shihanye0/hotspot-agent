import asyncio
from langchain.tools import tool
from scrapers.github_trending import fetch_github_trending
from scrapers.hacker_news import fetch_hacker_news
from scrapers.arxiv import fetch_arxiv_papers
from memory.chroma_client import check_ids_exist, add_items, search_similar


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        import concurrent.futures

        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result(timeout=30)


@tool
def tool_fetch_github_trending(language: str = "", since: str = "daily") -> str:
    """抓取 GitHub Trending 页面，获取当日热门仓库列表。

    Args:
        language: 编程语言过滤，为空则不限语言
        since: 时间范围 daily/weekly/monthly，默认 daily
    """
    try:
        items = _run_async(fetch_github_trending(language=language or "", since=since))
    except Exception as e:
        return f"GitHub 抓取失败: {e}"

    lines = []
    for item in items:
        stars = item.get("stars_today", "?")
        lang = item.get("language", "")
        lines.append(
            f"- [{item['name']}]({item['url']}) "
            f"| ⭐{stars} today | {lang}\n"
            f"  {item.get('description', '')}"
        )
    return "\n".join(lines) if lines else "今日无 GitHub 热门内容"


@tool
def tool_fetch_hacker_news(max_items: int = 10) -> str:
    """抓取 Hacker News 热门帖子中 AI 相关的内容。

    Args:
        max_items: 最大返回数量，默认 10
    """
    try:
        items = _run_async(fetch_hacker_news(max_items=max_items))
    except Exception as e:
        return f"Hacker News 抓取失败: {e}"

    lines = []
    for item in items:
        lines.append(
            f"- [{item['title']}]({item['url']}) | Score: {item['score']}"
        )
    return "\n".join(lines) if lines else "今日无 AI 相关 HN 热门帖子"


@tool
def tool_fetch_arxiv_papers(category: str = "cs.AI", max_results: int = 10) -> str:
    """抓取 ArXiv 最新 AI 论文。

    Args:
        category: 分类，可选 cs.AI/cs.CL/cs.CV/cs.LG，默认 cs.AI
        max_results: 最大返回数量，默认 10
    """
    try:
        items = _run_async(fetch_arxiv_papers(query=category, max_results=max_results))
    except Exception as e:
        return f"ArXiv 抓取失败: {e}"

    lines = []
    for item in items:
        lines.append(
            f"- [{item['title']}]({item['url']}) | {item.get('published', '')}"
        )
    return "\n".join(lines) if lines else "今日无 ArXiv 新论文"


@tool
def tool_query_memory(ids: str) -> str:
    """查询 ChromaDB 记忆库，检查哪些 ID 已经处理过（去重）。

    Args:
        ids: 逗号分隔的 ID 列表，例如 "github:user/repo,hn:12345,arxiv:2301.12345"
    """
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    existing = check_ids_exist(id_list)
    results = []
    for i in id_list:
        status = "已存在" if i in existing else "新内容"
        results.append(f"{i}: {status}")
    return "\n".join(results)


@tool
def tool_save_to_memory(items_json: str) -> str:
    """将已处理的内容存入 ChromaDB 记忆库，用于后续去重和检索。

    Args:
        items_json: JSON 数组字符串，每项包含 id, text, metadata 字段。
        例如: '[{"id": "github:x/y", "text": "描述", "metadata": {"source": "github"}}]'
    """
    import json

    try:
        data = json.loads(items_json)
        ids = [d["id"] for d in data]
        texts = [d["text"] for d in data]
        metadatas = [d.get("metadata", {}) for d in data]
        add_items(ids, texts, metadatas)
        return f"成功存储 {len(ids)} 条记录到记忆库"
    except json.JSONDecodeError as e:
        return f"JSON 解析失败: {e}"
    except Exception as e:
        return f"存储失败: {e}"


@tool
def tool_search_memory(query: str, n: int = 5) -> str:
    """在 ChromaDB 记忆库中搜索相似内容，用于回顾历史热点。

    Args:
        query: 搜索关键词
        n: 返回结果数量，默认 5
    """
    try:
        results = search_similar(query, n=n)
    except Exception as e:
        return f"搜索失败: {e}"

    lines = []
    for r in results:
        lines.append(f"- [{r['id']}] {r['document'][:100]} (相似度: {r['distance']:.3f})")
    return "\n".join(lines) if lines else "未找到相似内容"

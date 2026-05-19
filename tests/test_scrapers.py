"""爬虫模块测试 - 数据结构验证 + live smoke test"""
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_github_scraper_returns_list():
    """GitHub 爬虫返回列表（live test）"""
    from scrapers.github_trending import fetch_github_trending
    items = asyncio.run(fetch_github_trending())
    assert isinstance(items, list)
    # 网络不通时可能为空，不强制要求有数据


def test_github_scraper_item_structure():
    """GitHub 爬虫返回的数据项结构正确"""
    from scrapers.github_trending import fetch_github_trending
    items = asyncio.run(fetch_github_trending())
    if not items:
        return  # 网络不通时跳过
    required_keys = {"id", "name", "url", "description", "source"}
    for item in items:
        assert required_keys.issubset(item.keys())
        assert item["source"] == "github"
        assert item["id"].startswith("github:")
        assert item["url"].startswith("https://github.com/")


def test_hacker_news_scraper_returns_list():
    """HN 爬虫返回列表"""
    from scrapers.hacker_news import fetch_hacker_news
    items = asyncio.run(fetch_hacker_news(max_items=5))
    assert isinstance(items, list)


def test_hacker_news_item_structure():
    """HN 爬虫数据项结构正确"""
    from scrapers.hacker_news import fetch_hacker_news
    items = asyncio.run(fetch_hacker_news(max_items=5))
    if not items:
        return
    required_keys = {"id", "title", "url", "score", "source"}
    for item in items:
        assert required_keys.issubset(item.keys())
        assert item["source"] == "hackernews"
        assert item["id"].startswith("hn:")


def test_hacker_news_respects_max_items():
    """HN 爬虫尊重 max_items 限制"""
    from scrapers.hacker_news import fetch_hacker_news
    items = asyncio.run(fetch_hacker_news(max_items=3))
    assert len(items) <= 3


def test_arxiv_scraper_returns_list():
    """ArXiv 爬虫返回列表"""
    from scrapers.arxiv import fetch_arxiv_papers
    items = asyncio.run(fetch_arxiv_papers(max_results=5))
    assert isinstance(items, list)


def test_arxiv_item_structure():
    """ArXiv 爬虫数据项结构正确"""
    from scrapers.arxiv import fetch_arxiv_papers
    items = asyncio.run(fetch_arxiv_papers(max_results=5))
    if not items:
        return
    required_keys = {"id", "title", "url", "summary", "published", "source"}
    for item in items:
        assert required_keys.issubset(item.keys())
        assert item["source"] == "arxiv"
        assert item["id"].startswith("arxiv:")
        assert item["url"].startswith("https://arxiv.org/abs/")


def test_ai_keyword_filter():
    """AI 关键词过滤逻辑"""
    from scrapers.hacker_news import _is_ai_related
    assert _is_ai_related("New LLM model released")
    assert _is_ai_related("DeepSeek beats GPT")
    assert _is_ai_related("How to fine-tune transformers")
    assert not _is_ai_related("EA-18 fighter jets collide")
    assert not _is_ai_related("How to cook pasta")


def test_github_search_fallback():
    """GitHub Search API 回退（live test）"""
    from scrapers.github_trending import _fetch_via_search_api
    items = asyncio.run(_fetch_via_search_api())
    assert isinstance(items, list)
    if items:
        assert "id" in items[0]
        assert items[0]["source"] == "github"

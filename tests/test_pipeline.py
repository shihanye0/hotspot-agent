"""全流程集成测试"""
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def setup_function():
    import memory.chroma_client as mem
    base = os.path.dirname(os.path.dirname(__file__))
    mem.MEMORY_FILE = os.path.join(base, "memory.json")
    if os.path.exists(mem.MEMORY_FILE):
        os.remove(mem.MEMORY_FILE)


def teardown_function():
    import memory.chroma_client as mem
    if os.path.exists(mem.MEMORY_FILE):
        os.remove(mem.MEMORY_FILE)


def test_fetch_all_sources():
    """三源并行抓取不崩溃"""
    async def _test():
        from scrapers.github_trending import fetch_github_trending
        from scrapers.hacker_news import fetch_hacker_news
        from scrapers.arxiv import fetch_arxiv_papers

        results = await asyncio.gather(
            fetch_github_trending(),
            fetch_hacker_news(max_items=5),
            fetch_arxiv_papers(max_results=5),
            return_exceptions=True,
        )
        for r in results:
            if isinstance(r, Exception):
                print(f"Source failed (non-fatal): {r}")
            else:
                assert isinstance(r, list)
        return True

    assert asyncio.run(_test())


def test_dedup_flow():
    """去重流程：首次全部新内容，第二次全部去重"""
    from memory.chroma_client import add_items, check_ids_exist

    ids = ["github:a/b", "hn:123", "arxiv:2301.001"]
    texts = ["desc1", "desc2", "desc3"]
    metadatas = [{"s": "github"}, {"s": "hn"}, {"s": "arxiv"}]

    # 第一次：都没有
    assert check_ids_exist(ids) == set()

    # 存入
    add_items(ids, texts, metadatas)

    # 第二次：全部存在
    assert check_ids_exist(ids) == set(ids)


def test_report_generation():
    """报告生成使用正确的提示词模板"""
    from agent.prompts import REPORT_PROMPT

    assert "技术热点日报" in REPORT_PROMPT
    assert "GitHub" in REPORT_PROMPT
    assert "Hacker News" in REPORT_PROMPT
    assert "ArXiv" in REPORT_PROMPT
    assert "{raw_data}" in REPORT_PROMPT


def test_deepseek_connectivity():
    """DeepSeek API 可连通"""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

    llm = ChatOpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        model=DEEPSEEK_MODEL,
        temperature=0,
    )
    response = llm.invoke([HumanMessage(content="回复 'OK'")])
    assert len(response.content) > 0


def test_config_values():
    """配置值完整性检查"""
    from config import (
        DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
        CHROMA_COLLECTION, MAX_HISTORY_DAYS, MAX_ITEMS_PER_SOURCE,
    )
    assert DEEPSEEK_API_KEY.startswith("sk-")
    assert "deepseek" in DEEPSEEK_BASE_URL
    assert DEEPSEEK_MODEL == "deepseek-chat"
    assert MAX_HISTORY_DAYS > 0
    assert MAX_ITEMS_PER_SOURCE > 0

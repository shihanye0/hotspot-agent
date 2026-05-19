#!/usr/bin/env python
"""Hotspot Agent - 每日技术热点汇总 Agent

用法:
    python main.py           # 运行一次，生成日报
"""

import sys
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("hotspot-agent")


def run_pipeline():
    """直接 pipeline 运行（不依赖 LangGraph），稳定可靠"""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
    from agent.prompts import REPORT_PROMPT
    from memory.chroma_client import add_items, check_ids_exist
    from publishers.github_push import push_report
    from publishers.email_sender import send_report_email
    import asyncio

    today = datetime.now().strftime("%Y-%m-%d")
    logger.info("Step 1/5: 抓取数据...")

    async def fetch_all():
        from scrapers.github_trending import fetch_github_trending
        from scrapers.hacker_news import fetch_hacker_news
        from scrapers.arxiv import fetch_arxiv_papers

        async def safe(name, coro):
            try:
                return name, await coro
            except Exception as e:
                logger.warning(f"  {name} 失败: {e}")
                return name, []

        tasks = [
            safe("github", fetch_github_trending()),
            safe("hn", fetch_hacker_news()),
            safe("arxiv", fetch_arxiv_papers()),
        ]
        results = await asyncio.gather(*tasks)
        return dict(results)

    results = asyncio.run(fetch_all())

    # Build raw data
    parts = [f"# 原始数据快照 ({today})\n"]
    all_items = []
    for source, data in results.items():
        if not isinstance(data, list) or not data:
            continue
        parts.append(f"\n## {source.upper()}\n")
        for item in data:
            if source == "github":
                parts.append(
                    f"- [{item['name']}]({item['url']}) | ⭐{item.get('stars_today', '?')} | "
                    f"{item.get('language', '')}\n  {item.get('description', '')}"
                )
                all_items.append({
                    "id": item["id"],
                    "text": f"{item['name']}: {item.get('description', '')}",
                    "metadata": {"source": "github", "url": item["url"], "name": item["name"]},
                })
            elif source == "hn":
                parts.append(f"- [{item['title']}]({item['url']}) | Score: {item['score']}")
                all_items.append({
                    "id": item["id"],
                    "text": item["title"],
                    "metadata": {"source": "hackernews", "url": item["url"]},
                })
            elif source == "arxiv":
                parts.append(f"- [{item['title']}]({item['url']}) | {item.get('published', '')}")
                all_items.append({
                    "id": item["id"],
                    "text": f"{item['title']}: {item.get('summary', '')}",
                    "metadata": {"source": "arxiv", "url": item["url"]},
                })

    raw_data = "\n".join(parts)
    logger.info(f"  共抓取 {len(all_items)} 条")

    # Step 2: Dedup
    logger.info("Step 2/5: 去重检查...")
    ids = [item["id"] for item in all_items]
    existing = check_ids_exist(ids)
    new_items = [item for item in all_items if item["id"] not in existing]
    skipped = len(all_items) - len(new_items)
    logger.info(f"  跳过 {skipped} 条重复，{len(new_items)} 条新内容")

    if not new_items:
        logger.info("无新内容，跳过生成日报")
        return

    # Step 3: Generate report
    logger.info("Step 3/5: DeepSeek 生成日报...")
    llm = ChatOpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        model=DEEPSEEK_MODEL,
        temperature=0.3,
    )
    prompt = REPORT_PROMPT.format(raw_data=raw_data[:8000])
    response = llm.invoke([HumanMessage(content=prompt)])
    report = response.content.replace("YYYY-MM-DD", today)
    logger.info(f"  日报 {len(report)} 字符")

    # Save locally
    import os
    from config import REPORTS_DIR
    os.makedirs(REPORTS_DIR, exist_ok=True)
    filepath = f"{REPORTS_DIR}/{today}-daily-report.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"  保存到 {filepath}")

    # Step 4: Save memory
    logger.info("Step 4/5: 存入记忆库...")
    try:
        add_items(
            [item["id"] for item in new_items],
            [item["text"] for item in new_items],
            [item["metadata"] for item in new_items],
        )
        logger.info(f"  已存储 {len(new_items)} 条")
    except Exception as e:
        logger.warning(f"  记忆存储失败: {e}")

    # Step 5: Publish
    logger.info("Step 5/5: 发布...")
    try:
        push_report(report)
        logger.info("  GitHub 推送成功")
    except Exception as e:
        logger.warning(f"  GitHub 推送失败: {e}")

    try:
        send_report_email(report)
        logger.info("  邮件发送成功")
    except Exception as e:
        logger.warning(f"  邮件发送失败: {e}")

    logger.info("Hotspot Agent 完成!")


def main():
    logger.info("Hotspot Agent 启动")
    run_pipeline()


if __name__ == "__main__":
    main()

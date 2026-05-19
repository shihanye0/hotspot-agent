import json
from typing import TypedDict
from datetime import datetime
import asyncio

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from agent.tools import (
    tool_fetch_github_trending,
    tool_fetch_hacker_news,
    tool_fetch_arxiv_papers,
    tool_query_memory,
    tool_save_to_memory,
    tool_search_memory,
)
from agent.prompts import REPORT_PROMPT

ALL_TOOLS = [
    tool_fetch_github_trending,
    tool_fetch_hacker_news,
    tool_fetch_arxiv_papers,
    tool_query_memory,
    tool_save_to_memory,
    tool_search_memory,
]


class AgentState(TypedDict):
    messages: list
    raw_data: str
    report: str
    new_items: list
    publish_status: str


def get_llm():
    return ChatOpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        model=DEEPSEEK_MODEL,
        temperature=0.3,
    )


def _run_async(coro, timeout: int = 90):
    """运行异步协程并返回结果"""
    return asyncio.run(asyncio.wait_for(coro, timeout=timeout))


def fetch_data(state: AgentState) -> AgentState:
    """并行抓取所有数据源"""
    today = datetime.now().strftime("%Y-%m-%d")
    parts = [f"# 原始数据快照 ({today})\n"]

    async def gather():
        from scrapers.github_trending import fetch_github_trending
        from scrapers.hacker_news import fetch_hacker_news
        from scrapers.arxiv import fetch_arxiv_papers

        async def safe_fetch(name, coro):
            try:
                return name, await coro
            except Exception as e:
                return name, f"失败: {e}"

        tasks = [
            safe_fetch("github", fetch_github_trending()),
            safe_fetch("hn", fetch_hacker_news()),
            safe_fetch("arxiv", fetch_arxiv_papers()),
        ]
        results_list = await asyncio.gather(*tasks)
        return dict(results_list)

    try:
        results = _run_async(gather(), timeout=90)
    except Exception as e:
        return {**state, "raw_data": f"数据抓取失败: {e}", "new_items": []}

    all_items = []
    for source, data in results.items():
        if isinstance(data, list):
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
                    parts.append(
                        f"- [{item['title']}]({item['url']}) | Score: {item['score']}"
                    )
                    all_items.append({
                        "id": item["id"],
                        "text": item["title"],
                        "metadata": {"source": "hackernews", "url": item["url"]},
                    })
                elif source == "arxiv":
                    parts.append(
                        f"- [{item['title']}]({item['url']}) | {item.get('published', '')}"
                    )
                    all_items.append({
                        "id": item["id"],
                        "text": f"{item['title']}: {item.get('summary', '')}",
                        "metadata": {"source": "arxiv", "url": item["url"]},
                    })

    return {
        **state,
        "raw_data": "\n".join(parts),
        "new_items": all_items,
    }


def dedup(state: AgentState) -> AgentState:
    """去重检查"""
    items = state.get("new_items", [])
    if not items:
        return state

    ids = [item["id"] for item in items]
    from memory.chroma_client import check_ids_exist
    existing = check_ids_exist(ids)

    new_items = [item for item in items if item["id"] not in existing]
    skipped = len(items) - len(new_items)
    raw_data = state.get("raw_data", "")
    if skipped > 0:
        raw_data += f"\n\n> 去重：跳过 {skipped} 条已处理内容，{len(new_items)} 条新内容"
    else:
        raw_data += f"\n\n> 全部 {len(items)} 条为新内容"

    return {**state, "raw_data": raw_data, "new_items": new_items}


def should_publish(state: AgentState) -> str:
    """判断是否需要发布"""
    if state.get("new_items"):
        return "generate"
    return "skip"


def generate_report(state: AgentState) -> AgentState:
    """用 DeepSeek 生成日报"""
    llm = get_llm()
    raw_data = state.get("raw_data", "")
    prompt = REPORT_PROMPT.format(raw_data=raw_data[:8000])

    response = llm.invoke([HumanMessage(content=prompt)])
    report = response.content

    today = datetime.now().strftime("%Y-%m-%d")
    report = report.replace("YYYY-MM-DD", today)

    return {**state, "report": report}


def save_memory(state: AgentState) -> AgentState:
    """存入 ChromaDB 记忆"""
    items = state.get("new_items", [])
    if not items:
        return state

    try:
        from memory.chroma_client import add_items
        ids = [item["id"] for item in items]
        texts = [item["text"] for item in items]
        metadatas = [item["metadata"] for item in items]
        add_items(ids, texts, metadatas)
        return {**state, "publish_status": f"记忆库已存储 {len(ids)} 条"}
    except Exception as e:
        return {**state, "publish_status": f"记忆存储失败: {e}"}


def push_to_github(state: AgentState) -> AgentState:
    """推送日报到 GitHub"""
    report = state.get("report", "")
    if not report:
        return state

    try:
        from publishers.github_push import push_report
        push_report(report)
        return {**state, "publish_status": state.get("publish_status", "") + " | GitHub 推送成功"}
    except Exception as e:
        return {**state, "publish_status": state.get("publish_status", "") + f" | GitHub 推送失败: {e}"}


def send_email(state: AgentState) -> AgentState:
    """发送邮件通知"""
    report = state.get("report", "")
    if not report:
        return state

    try:
        from publishers.email_sender import send_report_email
        send_report_email(report)
        return {**state, "publish_status": state.get("publish_status", "") + " | 邮件发送成功"}
    except Exception as e:
        return {**state, "publish_status": state.get("publish_status", "") + f" | 邮件发送失败: {e}"}


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("fetch", fetch_data)
    workflow.add_node("dedup", dedup)
    workflow.add_node("generate", generate_report)
    workflow.add_node("save", save_memory)
    workflow.add_node("push", push_to_github)
    workflow.add_node("email", send_email)

    workflow.set_entry_point("fetch")
    workflow.add_edge("fetch", "dedup")
    workflow.add_conditional_edges(
        "dedup",
        should_publish,
        {"generate": "generate", "skip": END},
    )
    workflow.add_edge("generate", "save")
    workflow.add_edge("save", "push")
    workflow.add_edge("push", "email")
    workflow.add_edge("email", END)

    return workflow.compile()


def run_agent() -> dict:
    graph = build_graph()
    result = graph.invoke({"messages": [], "raw_data": "", "report": "", "new_items": [], "publish_status": ""})
    return result

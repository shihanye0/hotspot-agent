"""记忆模块 - 基于 JSON 文件的去重存储，简单可靠"""
import json
import os
from datetime import datetime, timedelta
from config import MAX_HISTORY_DAYS

MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory.json")


def _load() -> dict:
    if not os.path.exists(MEMORY_FILE):
        return {"ids": {}, "updated": ""}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict):
    # 清理超过 MAX_HISTORY_DAYS 的旧记录
    cutoff = (datetime.utcnow() - timedelta(days=MAX_HISTORY_DAYS)).isoformat()[:10]
    data["ids"] = {k: v for k, v in data["ids"].items() if v >= cutoff}
    data["updated"] = datetime.utcnow().isoformat()

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def check_ids_exist(ids: list[str]) -> set[str]:
    """检查哪些 ID 已经存在"""
    data = _load()
    return {i for i in ids if i in data["ids"]}


def add_items(ids: list[str], texts: list[str], metadatas: list[dict]):
    """将新项目存入记忆库"""
    data = _load()
    today = datetime.utcnow().isoformat()[:10]
    for item_id in ids:
        data["ids"][item_id] = today
    _save(data)


def search_similar(query: str, n: int = 5) -> list[dict]:
    """基于关键词的简单搜索"""
    data = _load()
    results = []
    query_lower = query.lower()
    for item_id, date in data["ids"].items():
        if query_lower in item_id.lower():
            results.append({
                "id": item_id,
                "document": item_id,
                "metadata": {"date": date},
                "distance": 0,
            })
        if len(results) >= n:
            break
    return results

"""记忆模块测试 - 去重存储"""
import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def setup_function():
    """每个测试前重置 memory.json"""
    base = os.path.dirname(os.path.dirname(__file__))
    mem_file = os.path.join(base, "memory.json")
    if os.path.exists(mem_file):
        os.remove(mem_file)
    # 重载模块以确保使用新的 memory.json
    import memory.chroma_client as mem
    mem.MEMORY_FILE = mem_file


def teardown_function():
    base = os.path.dirname(os.path.dirname(__file__))
    mem_file = os.path.join(base, "memory.json")
    if os.path.exists(mem_file):
        os.remove(mem_file)


def test_check_ids_empty():
    """空记忆库不返回任何 ID"""
    from memory.chroma_client import check_ids_exist
    existing = check_ids_exist(["a", "b", "c"])
    assert existing == set()


def test_add_and_check_ids():
    """存入后可以查到"""
    from memory.chroma_client import add_items, check_ids_exist
    add_items(["id1", "id2"], ["text1", "text2"], [{}, {}])
    existing = check_ids_exist(["id1", "id3"])
    assert existing == {"id1"}


def test_check_ids_skips_unknown():
    """数据库中不存在的 ID 不出现在结果中"""
    from memory.chroma_client import add_items, check_ids_exist
    add_items(["github:foo/bar"], ["desc"], [{"s": "github"}])
    result = check_ids_exist(["github:foo/bar", "hn:99999"])
    assert "github:foo/bar" in result
    assert "hn:99999" not in result


def test_add_items_preserves_data():
    """存储后的数据可被读取"""
    from memory.chroma_client import add_items, _load
    add_items(
        ["github:a/b"],
        ["A great repo"],
        [{"source": "github", "url": "https://github.com/a/b"}],
    )
    data = _load()
    assert "github:a/b" in data["ids"]


def test_second_run_dedup():
    """第二次运行可以看到重复的 ID"""
    from memory.chroma_client import add_items, check_ids_exist
    add_items(["id_a"], ["text"], [{}])
    # 模拟第二次运行
    existing = check_ids_exist(["id_a", "id_b"])
    assert "id_a" in existing
    assert "id_b" not in existing


def test_search_by_keyword():
    """关键词搜索"""
    from memory.chroma_client import add_items, search_similar
    add_items(
        ["github:openai/gpt-5", "github:facebook/react"],
        ["GPT-5", "React"],
        [{}, {}],
    )
    results = search_similar("gpt", n=5)
    assert len(results) >= 1
    assert any("openai" in r["id"] for r in results)

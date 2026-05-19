"""嵌入模块测试 - 哈希嵌入"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_embed_texts_returns_correct_shape():
    """返回正确的向量维度"""
    from memory.embeddings import embed_texts
    vectors = embed_texts(["hello", "world"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384


def test_embed_same_text_produces_same_vector():
    """相同文本产生相同向量"""
    from memory.embeddings import embed_texts
    v1 = embed_texts(["hello world"])
    v2 = embed_texts(["hello world"])
    assert v1 == v2


def test_embed_different_text_produces_different_vector():
    """不同文本产生不同向量"""
    from memory.embeddings import embed_texts
    v1 = embed_texts(["hello"])
    v2 = embed_texts(["world"])
    assert v1 != v2


def test_embed_empty_list():
    """空列表返回空"""
    from memory.embeddings import embed_texts
    result = embed_texts([])
    assert result == []


def test_embed_single_text():
    """单条文本"""
    from memory.embeddings import embed_texts
    result = embed_texts(["test"])
    assert len(result) == 1
    assert all(isinstance(x, float) for x in result[0])


def test_embed_values_in_range():
    """向量值在 [0, 1] 范围内"""
    from memory.embeddings import embed_texts
    vectors = embed_texts(["a", "b", "c"])
    for vec in vectors:
        for val in vec:
            assert 0.0 <= val <= 1.0

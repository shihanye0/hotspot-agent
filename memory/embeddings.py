"""嵌入模块 - 使用简单的哈希嵌入避免 sentence-transformers 线程安全问题"""

import hashlib


def get_embedding_model():
    return None


def embed_texts(texts: list[str]) -> list[list[float]]:
    """用文本哈希生成伪嵌入向量，规避 HuggingFace 下载问题。
    用于 ChromaDB 的语义去重——相同文本产生相同向量。
    """
    dim = 384
    vectors = []
    for text in texts:
        h = hashlib.sha256(text.encode()).digest()
        vec = []
        for i in range(0, len(h), 2):
            if len(vec) >= dim:
                break
            val = (h[i] * 256 + h[i + 1]) / 65535.0
            vec.append(val)
        while len(vec) < dim:
            vec.append(0.0)
        vectors.append(vec)
    return vectors

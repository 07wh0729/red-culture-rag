"""
嵌入向量模块 - 使用 sentence-transformers 本地生成向量
"""
from langchain_community.embeddings import HuggingFaceEmbeddings

import config


class EmbeddingModel:
    """本地嵌入模型封装"""

    def __init__(self, model_name: str = None, device: str = None):
        self.model_name = model_name or config.EMBEDDING_MODEL
        self.device = device or config.EMBEDDING_DEVICE
        self._model = None

    @property
    def model(self) -> HuggingFaceEmbeddings:
        if self._model is None:
            print(f"[i] 正在加载嵌入模型: {self.model_name} (device={self.device})")
            self._model = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={"device": self.device},
                encode_kwargs={
                    "normalize_embeddings": True,
                    "batch_size": 32,
                },
            )
            print(f"[v] 嵌入模型加载完成")
        return self._model

    def get_embeddings(self, texts: list) -> list:
        """批量获取文本向量"""
        return self.model.embed_documents(texts)

    def get_query_embedding(self, query: str) -> list:
        """获取查询向量"""
        return self.model.embed_query(query)
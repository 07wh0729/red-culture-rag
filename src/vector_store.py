"""
向量存储模块 - 基于 ChromaDB 的持久化向量库
"""
from pathlib import Path
from typing import List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document

import config
from .embeddings import EmbeddingModel


class VectorStore:
    """ChromaDB 向量存储封装"""

    def __init__(
        self,
        embedding_model: EmbeddingModel = None,
        persist_dir: str = None,
    ):
        self.embedding_model = embedding_model or EmbeddingModel()
        self.persist_dir = str(persist_dir or config.VECTORDB_DIR)
        self._store: Optional[Chroma] = None

    @property
    def store(self) -> Chroma:
        if self._store is None:
            self._store = Chroma(
                collection_name="red_culture_knowledge",
                embedding_function=self.embedding_model.model,
                persist_directory=self.persist_dir,
            )
        return self._store

    def clear(self):
        """清空向量库"""
        import shutil
        if Path(self.persist_dir).exists():
            shutil.rmtree(self.persist_dir, ignore_errors=True)
        self._store = None
        print("[v] 向量库已清空")

    def add_documents(self, documents: List[Document], batch_size: int = 50):
        """批量添加文档到向量库"""
        total = len(documents)
        for i in range(0, total, batch_size):
            batch = documents[i:i + batch_size]
            self.store.add_documents(batch)
            progress = min(i + batch_size, total)
            print(f"  [i] 向量化进度: {progress}/{total}")
        print(f"[v] 已入库 {total} 条文档块")

    def search(
        self,
        query: str,
        top_k: int = None,
        metadata_filter: dict = None,
    ) -> List[Document]:
        """相似度检索"""
        top_k = top_k or config.TOP_K
        search_kwargs = {"k": top_k}
        if metadata_filter:
            search_kwargs["filter"] = metadata_filter
        retriever = self.store.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs,
        )
        return retriever.invoke(query)

    def document_count(self) -> int:
        """返回向量库中的文档数量"""
        try:
            return self.store._collection.count()
        except Exception:
            return 0
"""
检索器模块 - 多策略检索
"""
from typing import List

from langchain_core.documents import Document

import config
from .vector_store import VectorStore


class Retriever:
    """文档检索器，支持相似度检索和 MMR 多样性检索"""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.top_k = config.TOP_K

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        search_type: str = "similarity",
    ) -> List[Document]:
        """
        检索相关文档
        search_type: "similarity" (相似度) | "mmr" (最大边际相关性，结果更多样)
        """
        top_k = top_k or self.top_k
        if search_type == "mmr":
            retriever = self.vector_store.store.as_retriever(
                search_type="mmr",
                search_kwargs={"k": top_k, "fetch_k": top_k * 3},
            )
        else:
            retriever = self.vector_store.store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": top_k},
            )
        docs = retriever.invoke(query)
        return docs

    def retrieve_with_scores(self, query: str, top_k: int = None):
        """检索并返回相似度分数"""
        top_k = top_k or self.top_k
        results = self.vector_store.store.similarity_search_with_score(
            query, k=top_k
        )
        return results

    def format_context(self, docs: List[Document]) -> str:
        """将检索到的文档拼接为上下文字符串"""
        parts = []
        for idx, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "未知")
            parts.append(f"[参考 {idx}] 来源: {source}\n{doc.page_content}")
        return "\n\n---\n\n".join(parts)
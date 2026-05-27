"""
RAG 管道 - 整合文档加载、分割、向量化、检索、生成的全流程
"""
from typing import List, Optional

from langchain_core.documents import Document

from .document_loader import DocumentLoader
from .text_splitter import TextSplitter
from .embeddings import EmbeddingModel
from .vector_store import VectorStore
from .retriever import Retriever
from .generator import Generator

import config


class RAGPipeline:
    """RAG 全流程管道"""

    def __init__(
        self,
        data_dir: str = None,
        vector_db_dir: str = None,
    ):
        self.data_dir = data_dir or str(config.DATA_DIR)
        self.vector_db_dir = vector_db_dir or str(config.VECTORDB_DIR)
        self._loader: Optional[DocumentLoader] = None
        self._splitter: Optional[TextSplitter] = None
        self._embedder: Optional[EmbeddingModel] = None
        self._vector_store: Optional[VectorStore] = None
        self._retriever: Optional[Retriever] = None
        self._generator: Optional[Generator] = None

    @property
    def loader(self) -> DocumentLoader:
        if self._loader is None:
            self._loader = DocumentLoader(self.data_dir)
        return self._loader

    @property
    def splitter(self) -> TextSplitter:
        if self._splitter is None:
            self._splitter = TextSplitter()
        return self._splitter

    @property
    def embedder(self) -> EmbeddingModel:
        if self._embedder is None:
            self._embedder = EmbeddingModel()
        return self._embedder

    @property
    def vector_store(self) -> VectorStore:
        if self._vector_store is None:
            self._vector_store = VectorStore(
                embedding_model=self.embedder,
                persist_dir=self.vector_db_dir,
            )
        return self._vector_store

    @property
    def retriever(self) -> Retriever:
        if self._retriever is None:
            self._retriever = Retriever(self.vector_store)
        return self._retriever

    @property
    def generator(self) -> Generator:
        if self._generator is None:
            self._generator = Generator()
        return self._generator

    def build_index(self, clear_first: bool = True):
        """构建/重建向量索引：加载 -> 分割 -> 向量化 -> 入库"""
        print("\n" + "=" * 60)
        print("  开始构建知识库索引")
        print("=" * 60)
        if clear_first:
            self.vector_store.clear()
        print("\n[1/4] 加载文档...")
        docs = self.loader.load_all()
        if not docs:
            print("[!] 没有找到可加载的文档，请将知识文档放入 data/ 目录")
            return
        print(f"  共加载 {len(docs)} 个文档段")
        print("\n[2/4] 文本分割...")
        chunks = self.splitter.split(docs)
        print("\n[3/4] 向量化并写入向量库...")
        self.vector_store.add_documents(chunks)
        count = self.vector_store.document_count()
        print(f"\n[4/4] 索引构建完成！向量库现有 {count} 条记录")
        print("=" * 60 + "\n")

    def ask(
        self,
        question: str,
        top_k: int = None,
        include_sources: bool = False,
    ):
        """RAG 问答"""
        docs = self.retriever.retrieve(question, top_k=top_k)
        context = self.retriever.format_context(docs)
        answer = self.generator.generate(question, context=context)
        if include_sources:
            return {
                "question": question,
                "answer": answer,
                "sources": [
                    {
                        "content": d.page_content[:200],
                        "source": d.metadata.get("source", ""),
                    }
                    for d in docs
                ],
            }
        return answer

    def quiz(
        self,
        topic: str = "",
        num_questions: int = 3,
        question_type: str = "choice",
    ) -> str:
        """随机出题：先检索相关知识，再基于知识生成题目"""
        if not topic:
            topic = "红色文化"
        docs = self.retriever.retrieve(topic, top_k=3)
        context = self.retriever.format_context(docs)
        quiz_text = self.generator.generate_quiz(
            context=context,
            num_questions=num_questions,
            question_type=question_type,
        )
        return quiz_text

    def explain(self, concept: str) -> str:
        """讲解指定知识点"""
        docs = self.retriever.retrieve(concept, top_k=3)
        context = self.retriever.format_context(docs)
        return self.generator.explain_concept(concept, context=context)

    def status(self) -> dict:
        """返回管道状态"""
        return {
            "data_dir": self.data_dir,
            "vector_db_dir": self.vector_db_dir,
            "document_count": self.vector_store.document_count(),
            "embedding_model": config.EMBEDDING_MODEL,
            "llm_model": config.LLM_MODEL,
        }

    def search_docs(self, query: str, top_k: int = None) -> List[Document]:
        """仅检索，不生成"""
        return self.retriever.retrieve(query, top_k=top_k)
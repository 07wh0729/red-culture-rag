"""
RAG 管道 v2 - 整合文档加载、分割、向量化、检索、溯源问答、测验、多媒体
"""
from typing import List, Optional

from langchain_core.documents import Document

from .document_loader import DocumentLoader
from .text_splitter import TextSplitter
from .embeddings import EmbeddingModel
from .vector_store import VectorStore
from .retriever import Retriever
from .generator import Generator
from .quiz_engine import QuizEngine, Question
from .media_manager import MediaManager
from .tts_service import TTSService

import config


class RAGPipeline:
    """RAG 全流程管道 v2"""

    def __init__(self, data_dir: str = None, vector_db_dir: str = None):
        self.data_dir = data_dir or str(config.DATA_DIR)
        self.vector_db_dir = vector_db_dir or str(config.VECTORDB_DIR)

        self._loader = None
        self._splitter = None
        self._embedder = None
        self._vector_store = None
        self._retriever = None
        self._generator = None
        self._quiz_engine = None
        self._media_manager = None
        self._tts = None

    @property
    def loader(self): 
        if self._loader is None: self._loader = DocumentLoader(self.data_dir)
        return self._loader

    @property
    def splitter(self):
        if self._splitter is None: self._splitter = TextSplitter()
        return self._splitter

    @property
    def embedder(self):
        if self._embedder is None: self._embedder = EmbeddingModel()
        return self._embedder

    @property
    def vector_store(self):
        if self._vector_store is None:
            self._vector_store = VectorStore(embedding_model=self.embedder, persist_dir=self.vector_db_dir)
        return self._vector_store

    @property
    def retriever(self):
        if self._retriever is None: self._retriever = Retriever(self.vector_store)
        return self._retriever

    @property
    def generator(self):
        if self._generator is None: self._generator = Generator()
        return self._generator

    @property
    def quiz_engine(self):
        if self._quiz_engine is None: self._quiz_engine = QuizEngine(self.generator)
        return self._quiz_engine

    @property
    def media(self):
        if self._media_manager is None: self._media_manager = MediaManager()
        return self._media_manager

    @property
    def tts(self):
        if self._tts is None: self._tts = TTSService()
        return self._tts

    # ===== 建库 =====

    def build_index(self, clear_first: bool = True):
        """构建向量索引"""
        print("\n" + "=" * 60)
        print("  开始构建知识库索引")
        print("=" * 60)
        if clear_first:
            self.vector_store.clear()
        print("\n[1/4] 加载文档...")
        docs = self.loader.load_all()
        if not docs:
            print("[!] 没有找到可加载的文档")
            return
        print(f"  共加载 {len(docs)} 个文档段")
        print("\n[2/4] 文本分割...")
        chunks = self.splitter.split(docs)
        print("\n[3/4] 向量化并写入向量库...")
        self.vector_store.add_documents(chunks)
        count = self.vector_store.document_count()
        print(f"\n[4/4] 索引构建完成！向量库现有 {count} 条记录")
        print("=" * 60 + "\n")

    # ===== 问答 =====

    def ask(self, question: str, top_k: int = None) -> dict:
        """RAG 问答 - 带溯源引用"""
        top_k = top_k or config.TOP_K
        docs = self.retriever.retrieve(question, top_k=top_k)
        context = self.retriever.format_context(docs)
        result = self.generator.generate(question, context=context)

        sources = []
        for d in docs:
            sources.append({
                "source": d.metadata.get("source", "未知"),
                "snippet": d.page_content[:200],
            })

        keywords = list(set(question[:20].split()))[:5]
        related_media = self.media.search_related(keywords, limit=3)

        return {
            "question": question,
            "answer": result["answer"],
            "model": result["model"],
            "sources": sources,
            "related_media": [
                {"id": m["id"], "title": m["title"], "type": m["type"], "path": m["path"]}
                for m in related_media
            ],
        }

    # ===== 测验 =====

    def quiz_generate(self, topic: str = "", num: int = 5, qtype: str = "single") -> dict:
        """生成测验"""
        if not topic:
            topic = "红色文化"
        docs = self.retriever.retrieve(topic, top_k=3)
        context = self.retriever.format_context(docs)
        questions = self.quiz_engine.generate(context, num, qtype)
        return {
            "topic": topic,
            "total": len(questions),
            "questions": [
                {
                    "id": q.id, "type": q.type, "stem": q.stem,
                    "options": q.options,
                }
                for q in questions
            ],
        }

    def quiz_answer(self, question_id: int, answer: str):
        """提交答案"""
        self.quiz_engine.submit_answer(question_id, answer)

    def quiz_grade(self) -> dict:
        """判分"""
        return self.quiz_engine.grade()

    def quiz_reset(self):
        """重置测验"""
        self.quiz_engine.reset()

    def quiz_get_wrong(self) -> list:
        """获取错题"""
        return self.quiz_engine.get_wrong_questions()

    # ===== 知识点讲解 =====

    def explain(self, concept: str) -> dict:
        """讲解知识点"""
        docs = self.retriever.retrieve(concept, top_k=3)
        context = self.retriever.format_context(docs)
        result = self.generator.explain_concept(concept, context)

        sources = [
            {"source": d.metadata.get("source", ""), "snippet": d.page_content[:150]}
            for d in docs
        ]
        keywords = concept.split()[:5]
        related_media = self.media.search_related(keywords, limit=3)

        return {
            "concept": concept,
            "explanation": result["answer"],
            "sources": sources,
            "related_media": [
                {"id": m["id"], "title": m["title"], "type": m["type"], "path": m["path"]}
                for m in related_media
            ],
        }

    # ===== 语音播报 =====

    def narrate(self, text: str, title: str = "红色故事播报") -> dict:
        """文字转语音"""
        result = self.tts.narrate_story(text, title)
        if result:
            return {"status": "success", "audio": result}
        return {"status": "error", "message": "语音合成失败"}

    # ===== 多媒体 =====

    def media_list(self, media_type: str = None, tag: str = None) -> list:
        return self.media.list(media_type, tag)

    def media_add(self, file_path: str, title: str = "", tags: list = None) -> dict:
        return self.media.add(file_path, title, tags or [])

    def media_delete(self, file_id: str) -> bool:
        return self.media.delete(file_id)

    def media_update(self, file_id: str, title: str = None, tags: list = None) -> bool:
        return self.media.update(file_id, title, tags)

    # ===== 工具 =====

    def search_docs(self, query: str, top_k: int = None) -> list:
        docs = self.retriever.retrieve(query, top_k=top_k)
        return [
            {"content": d.page_content, "source": d.metadata.get("source", "")}
            for d in docs
        ]

    def status(self) -> dict:
        return {
            "data_dir": self.data_dir,
            "vector_db_dir": self.vector_db_dir,
            "document_count": self.vector_store.document_count(),
            "embedding_model": config.EMBEDDING_MODEL,
            "llm_model": config.LLM_MODEL,
            "media_count": {
                "images": len(self.media.list("images")),
                "videos": len(self.media.list("videos")),
                "audio": len(self.media.list("audio")),
            },
        }
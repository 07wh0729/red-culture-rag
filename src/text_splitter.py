"""
文本分割模块 - 将长文档切分为适合检索的语义块
"""
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

import config


class TextSplitter:
    """递归字符分割器，对中文友好"""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP

        self.separators = [
            "\n\n", "\n", "。", "！", "？", "；", "，", " ", ""
        ]

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
        )

    def split(self, documents: List[Document]) -> List[Document]:
        """分割文档列表"""
        chunks = self.splitter.split_documents(documents)
        print(f"[v] 文档分割完成: {len(documents)} 段 -> {len(chunks)} 块")
        return chunks
"""
文档加载模块 - 支持 txt, md, pdf, docx 等格式
"""
import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
)
from langchain_core.documents import Document


class DocumentLoader:
    """统一文档加载器，支持多种格式"""

    SUPPORTED_EXT = {
        ".txt": "text",
        ".md": "markdown",
        ".pdf": "pdf",
        ".docx": "docx",
    }

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)

    def list_files(self) -> List[Path]:
        """列出所有支持的文档文件"""
        files = []
        for ext in self.SUPPORTED_EXT:
            files.extend(self.data_dir.glob(f"*{ext}"))
        return sorted(files)

    def load_file(self, file_path: Path) -> List[Document]:
        """加载单个文件"""
        ext = file_path.suffix.lower()
        if ext not in self.SUPPORTED_EXT:
            raise ValueError(f"不支持的文件格式: {ext}")

        if ext == ".txt":
            loader = TextLoader(str(file_path), encoding="utf-8")
        elif ext == ".pdf":
            loader = PyPDFLoader(str(file_path))
        elif ext == ".docx":
            loader = Docx2txtLoader(str(file_path))
        elif ext == ".md":
            loader = UnstructuredMarkdownLoader(str(file_path))
        else:
            raise ValueError(f"未处理的格式: {ext}")

        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = file_path.name
            doc.metadata["file_type"] = self.SUPPORTED_EXT[ext]
        return docs

    def load_all(self) -> List[Document]:
        """加载 data 目录下所有文档"""
        all_docs = []
        files = self.list_files()
        if not files:
            print(f"[!] 警告: {self.data_dir} 目录下没有找到支持的文档")
            return all_docs

        for fp in files:
            try:
                docs = self.load_file(fp)
                all_docs.extend(docs)
                print(f"[v] 已加载: {fp.name} ({len(docs)} 段)")
            except Exception as exc:
                print(f"[x] 加载失败 {fp.name}: {exc}")
        return all_docs
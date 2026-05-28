"""
全局配置文件
"""
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
VECTORDB_DIR = ROOT_DIR / "vectordb" / "chroma"

EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
EMBEDDING_DEVICE = "cpu"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80

TOP_K = 5

# DeepSeek 大模型配置
LLM_PROVIDER = "deepseek"
LLM_MODEL = "deepseek-chat"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-8b62f55e436a42d9a92e2bfb2fd8bb17")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

# 兼容旧环境变量
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")

API_HOST = "0.0.0.0"
API_PORT = 8000
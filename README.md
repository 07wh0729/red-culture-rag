# 红色文化智能学习平台 - RAG 框架

基于 RAG（检索增强生成）技术的红色文化知识学习系统框架。

## 项目结构

`
red-culture-rag/
├── app.py                    # 入口（serve/cli/build 三种模式）
├── config.py                 # 全局配置
├── requirements.txt          # Python 依赖
├── data/                     # 知识库文档目录
│   ├── party_history.txt     # 党史知识（示例）
│   └── heroes.txt            # 英烈事迹（示例）
├── vectordb/                 # 向量库持久化目录（自动生成）
└── src/                      # 核心源码
    ├── document_loader.py    # 多格式文档加载（txt/md/pdf/docx）
    ├── text_splitter.py      # 自适应文本分割
    ├── embeddings.py         # 嵌入模型（本地 sentence-transformers）
    ├── vector_store.py       # ChromaDB 向量存储
    ├── retriever.py          # 检索器（相似度 / MMR）
    ├── generator.py          # LLM 生成（问答/出题/讲解）
    ├── rag_pipeline.py       # RAG 全流程管道
    └── api.py                # FastAPI REST 接口
`

## 快速开始

### 1. 安装依赖

`ash
cd red-culture-rag
pip install -r requirements.txt
`

### 2. 放入知识文档

将党史、红色故事、英烈事迹等文档（支持 .txt / .md / .pdf / .docx）放入 data/ 目录。

### 3. 构建索引

`ash
python app.py build
`

### 4. 启动服务

`ash
# API 模式
python app.py serve
# 访问 http://localhost:8000/docs 查看接口文档

# 命令行交互模式
python app.py cli
`

## 核心功能

| 功能 | API | CLI 命令 |
|------|-----|----------|
| RAG 问答 | POST /ask | sk <问题> |
| 随机出题 | POST /quiz | quiz [主题] |
| 知识点讲解 | POST /explain | explain <概念> |
| 文档检索 | GET /search | search <关键词> |
| 构建索引 | POST /build | uild |

## 技术栈

- **RAG 框架**: LangChain
- **向量模型**: BAAI/bge-small-zh-v1.5（中文优化，本地运行）
- **向量库**: ChromaDB（本地持久化）
- **LLM**: OpenAI GPT-4o-mini（可替换为其他兼容 API）
- **API**: FastAPI + Uvicorn

## 配置说明

编辑 config.py 可调整：
- EMBEDDING_MODEL - 嵌入模型
- CHUNK_SIZE / CHUNK_OVERLAP - 文本分块参数
- TOP_K - 检索返回数
- LLM_MODEL - 大模型选择
- OPENAI_API_KEY / OPENAI_BASE_URL - API 密钥（可设置环境变量）

## 注意事项

- 首次运行 uild 时会自动下载嵌入模型（约 100MB）
- LLM 调用需要有效的 OpenAI API Key 或兼容的 API 端点
- Python 版本要求 >= 3.10

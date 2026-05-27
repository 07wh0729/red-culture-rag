"""
FastAPI 接口层 - 提供 RESTful API
"""
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .rag_pipeline import RAGPipeline

import config


pipeline: RAGPipeline = None


def get_pipeline() -> RAGPipeline:
    global pipeline
    if pipeline is None:
        pipeline = RAGPipeline()
    return pipeline


app = FastAPI(
    title="红色文化智能学习平台 - RAG API",
    description="基于 RAG 技术的红色文化知识问答、讲解、出题系统",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    include_sources: bool = True


class QuizRequest(BaseModel):
    topic: str = "红色文化"
    num_questions: int = 3
    question_type: str = "choice"


class ExplainRequest(BaseModel):
    concept: str


@app.get("/")
def root():
    return {
        "name": "红色文化智能学习平台 RAG API",
        "version": "1.0.0",
        "endpoints": [
            "POST /ask        - RAG 问答",
            "POST /quiz       - 随机出题",
            "POST /explain    - 知识点讲解",
            "POST /build      - 构建/重建索引",
            "GET  /status     - 系统状态",
            "GET  /search     - 文档检索",
        ],
    }


@app.post("/ask")
def ask_question(req: AskRequest):
    """RAG 问答接口"""
    pipe = get_pipeline()
    try:
        result = pipe.ask(
            question=req.question,
            top_k=req.top_k,
            include_sources=req.include_sources,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/quiz")
def generate_quiz(req: QuizRequest):
    """随机出题接口"""
    pipe = get_pipeline()
    try:
        result = pipe.quiz(
            topic=req.topic,
            num_questions=req.num_questions,
            question_type=req.question_type,
        )
        return {"topic": req.topic, "quiz": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/explain")
def explain_concept(req: ExplainRequest):
    """知识点讲解接口"""
    pipe = get_pipeline()
    try:
        result = pipe.explain(concept=req.concept)
        return {"concept": req.concept, "explanation": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/build")
def build_index():
    """构建/重建知识库索引"""
    pipe = get_pipeline()
    try:
        pipe.build_index(clear_first=True)
        return {
            "status": "success",
            "message": "索引构建完成",
            "document_count": pipe.vector_store.document_count(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
def system_status():
    """系统状态查询"""
    pipe = get_pipeline()
    return pipe.status()


@app.get("/search")
def search_docs(
    query: str = Query(..., description="搜索关键词"),
    top_k: int = Query(5, description="返回数量"),
):
    """文档检索（不含生成）"""
    pipe = get_pipeline()
    try:
        docs = pipe.search_docs(query, top_k=top_k)
        return {
            "query": query,
            "results": [
                {
                    "content": d.page_content,
                    "source": d.metadata.get("source", ""),
                }
                for d in docs
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
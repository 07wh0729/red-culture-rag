"""
FastAPI 接口层 v2 - 完整红色文化学习平台 API
"""
import os
import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
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
    title="红色文化智能学习平台 API",
    description="基于 RAG 技术的红色文化知识问答、测验、多媒体学习系统",
    version="2.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 静态文件
frontend_dir = config.ROOT_DIR / "frontend"
media_dir = config.ROOT_DIR / "media"
uploads_dir = config.ROOT_DIR / "uploads"
for d in [frontend_dir, media_dir, uploads_dir]:
    d.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")


# ===== 请求模型 =====

class AskRequest(BaseModel):
    question: str
    top_k: int = 5

class QuizAnswerRequest(BaseModel):
    question_id: int
    answer: str

class NarrateRequest(BaseModel):
    text: str
    title: str = "红色故事播报"

class MediaUpdateRequest(BaseModel):
    title: str = None
    tags: List[str] = None


# ===== 页面路由 =====

@app.get("/", response_class=HTMLResponse)
def index():
    """学习平台主页"""
    return FileResponse(str(frontend_dir / "index.html"))

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    """后台管理页面"""
    return FileResponse(str(frontend_dir / "admin" / "index.html"))


# ===== 问答 =====

@app.post("/api/ask")
def ask_question(req: AskRequest):
    """RAG 智能问答"""
    pipe = get_pipeline()
    try:
        return pipe.ask(req.question, req.top_k)
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.post("/api/explain")
def explain_concept(req: AskRequest):
    """知识点讲解"""
    pipe = get_pipeline()
    try:
        return pipe.explain(req.question)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ===== 测验 =====

@app.post("/api/quiz/generate")
def quiz_generate(topic: str = Form("红色文化"), num: int = Form(5), qtype: str = Form("single")):
    """生成测验题目"""
    pipe = get_pipeline()
    try:
        return pipe.quiz_generate(topic, num, qtype)
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.post("/api/quiz/answer")
def quiz_answer(req: QuizAnswerRequest):
    """提交答案"""
    pipe = get_pipeline()
    try:
        pipe.quiz_answer(req.question_id, req.answer)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.post("/api/quiz/grade")
def quiz_grade():
    """判分并获取结果"""
    pipe = get_pipeline()
    try:
        return pipe.quiz_grade()
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.post("/api/quiz/reset")
def quiz_reset():
    """重置测验"""
    pipe = get_pipeline()
    pipe.quiz_reset()
    return {"status": "ok"}

@app.get("/api/quiz/wrong")
def quiz_wrong():
    """获取错题"""
    pipe = get_pipeline()
    return pipe.quiz_get_wrong()


# ===== 语音播报 =====

@app.post("/api/narrate")
def narrate(req: NarrateRequest):
    """文字转语音"""
    pipe = get_pipeline()
    try:
        result = pipe.narrate(req.text, req.title)
        return result
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ===== 多媒体资源 =====

@app.get("/api/media")
def media_list(
    type: str = Query(None, alias="type"),
    tag: str = Query(None),
):
    """列出媒体资源"""
    pipe = get_pipeline()
    return pipe.media_list(type, tag)

@app.post("/api/media/upload")
async def media_upload(
    file: UploadFile = File(...),
    title: str = Form(""),
    tags: str = Form(""),
):
    """上传媒体资源"""
    pipe = get_pipeline()
    try:
        ext = Path(file.filename).suffix
        file_id = uuid.uuid4().hex[:12]
        save_path = uploads_dir / f"{file_id}{ext}"
        content = await file.read()
        save_path.write_bytes(content)

        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        entry = pipe.media_add(str(save_path), title or file.filename, tag_list)
        return {"status": "success", "entry": entry}
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.delete("/api/media/{file_id}")
def media_delete(file_id: str):
    """删除媒体资源"""
    pipe = get_pipeline()
    ok = pipe.media_delete(file_id)
    if not ok:
        raise HTTPException(404, "资源不存在")
    return {"status": "deleted"}

@app.put("/api/media/{file_id}")
def media_update(file_id: str, req: MediaUpdateRequest):
    """更新媒体资源信息"""
    pipe = get_pipeline()
    ok = pipe.media_update(file_id, req.title, req.tags)
    if not ok:
        raise HTTPException(404, "资源不存在")
    return {"status": "updated"}


# ===== 文档管理 =====

@app.post("/api/docs/upload")
async def docs_upload(file: UploadFile = File(...)):
    """上传知识文档到 data 目录"""
    try:
        save_path = config.DATA_DIR / file.filename
        content = await file.read()
        save_path.write_bytes(content)
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.get("/api/docs")
def docs_list():
    """列出知识库文档"""
    pipe = get_pipeline()
    files = pipe.loader.list_files()
    return [{"name": f.name, "size": f.stat().st_size} for f in files]

@app.delete("/api/docs/{filename}")
def docs_delete(filename: str):
    """删除知识文档"""
    file_path = config.DATA_DIR / filename
    if not file_path.exists():
        raise HTTPException(404, "文档不存在")
    file_path.unlink()
    return {"status": "deleted"}


# ===== 索引管理 =====

@app.post("/api/build")
def build_index():
    """构建/重建知识库索引"""
    pipe = get_pipeline()
    try:
        pipe.build_index(clear_first=True)
        return {"status": "success", "document_count": pipe.vector_store.document_count()}
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.get("/api/status")
def system_status():
    """系统状态"""
    pipe = get_pipeline()
    return pipe.status()

@app.get("/api/search")
def search_docs(query: str = Query(...), top_k: int = Query(5)):
    """文档检索"""
    pipe = get_pipeline()
    return {"query": query, "results": pipe.search_docs(query, top_k)}
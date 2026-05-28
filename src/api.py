"""
FastAPI 接口层 v2 - 全中文 Swagger
"""
import os
import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query, Path as FPath, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from .rag_pipeline import RAGPipeline

import config

pipeline: RAGPipeline = None


def get_pipeline() -> RAGPipeline:
    global pipeline
    if pipeline is None:
        pipeline = RAGPipeline()
    return pipeline


# 自定义中文 Swagger HTML
ZH_SWAGGER_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><title>红色文化智能学习平台 - API 文档</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
<style>html{box-sizing:border-box;overflow-y:scroll}*,*:before,*:after{box-sizing:inherit}body{margin:0;background:#fafafa}.topbar{display:none}.swagger-ui .info .title{color:#C41E3A}</style>
</head>
<body><div id="swagger-ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
SwaggerUIBundle({url:"/openapi.json",dom_id:"#swagger-ui",deepLinking:true,defaultModelsExpandDepth:1,defaultModelExpandDepth:2,docExpansion:"list",displayOperationId:false,layout:"BaseLayout",presets:[SwaggerUIBundle.presets.apis]});
setTimeout(function(){
var t={"Schemas":"数据模型","Expand all":"全部展开","Collapse all":"全部折叠","Example Value":"示例值","Schema":"模型","No parameters":"无参数","Request body":"请求体","Responses":"响应","Body":"请求体","Try it out":"试一试","Cancel":"取消","Execute":"执行","Clear":"清除","Download":"下载","Close":"关闭","Copy":"复制","Copied":"已复制","Send Request":"发送请求","Authorize":"认证","Available authorizations":"可用认证","number":"数字","string":"字符串","boolean":"布尔","integer":"整数","array":"数组","object":"对象","null":"空值","Value":"值","Description":"描述","Deprecated":"已弃用","Required":"必填","nullable":"可空","default":"默认值","example":"示例","minimum":"最小值","maximum":"最大值","minLength":"最小长度","maxLength":"最大长度","pattern":"格式","enum":"枚举"};function r(e){if(e.nodeType===1){if(e.childNodes)e.childNodes.forEach(r);var a=e.textContent||'';for(var k in t)if(a.trim()===k)e.textContent=t[k]}}setInterval(function(){r(document.querySelector('.swagger-ui')||document.body)},600)},1200);
</script></body></html>'''


app = FastAPI(
    title="红色文化智能学习平台 API",
    description="基于 RAG 技术的红色文化知识问答、在线测验、多媒体学习系统",
    version="2.0.0",
    docs_url=None,
    redoc_url="/redoc",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

frontend_dir = config.ROOT_DIR / "frontend"
media_dir = config.ROOT_DIR / "media"
uploads_dir = config.ROOT_DIR / "uploads"
for d in [frontend_dir, media_dir, uploads_dir]:
    d.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")


@app.get("/docs", include_in_schema=False)
async def swagger_zh():
    """中文 Swagger 文档页面"""
    return HTMLResponse(ZH_SWAGGER_HTML)


# ===== 模型 =====

class AskRequest(BaseModel):
    model_config = {"title": "问答请求"}
    question: str = Field(..., description="用户提问内容")
    top_k: int = Field(5, description="检索返回的文档数量", ge=1, le=20)


class QuizAnswerRequest(BaseModel):
    model_config = {"title": "作答请求"}
    question_id: int = Field(..., description="题目编号")
    answer: str = Field(..., description="作答内容（单选填字母，多选用逗号分隔，简答填文本）")


class NarrateRequest(BaseModel):
    model_config = {"title": "播报请求"}
    text: str = Field(..., description="待朗读的文本内容")
    title: str = Field("红色故事播报", description="播报标题")


class MediaUpdateRequest(BaseModel):
    model_config = {"title": "媒体更新请求"}
    title: Optional[str] = Field(None, description="新的资源标题")
    tags: Optional[List[str]] = Field(None, description="新的标签列表")


# ===== 页面 =====

@app.get("/", response_class=HTMLResponse, tags=["页面"], summary="学习平台主页")
def index():
    return FileResponse(str(frontend_dir / "index.html"))


@app.get("/admin", response_class=HTMLResponse, tags=["页面"], summary="后台管理页面")
def admin_page():
    return FileResponse(str(frontend_dir / "admin" / "index.html"))


# ===== 智能问答 =====

@app.post("/api/ask", tags=["智能问答"], operation_id="rag_智能问答",
    summary="RAG 智能问答", description="基于知识库语义检索，结合大模型生成答案。回答强制标注来源，杜绝 AI 幻觉。")
def ask_question(req: AskRequest):
    pipe = get_pipeline()
    try: return pipe.ask(req.question, req.top_k)
    except Exception as e: raise HTTPException(500, detail=str(e))


@app.post("/api/explain", tags=["智能问答"], operation_id="讲解知识点",
    summary="知识点讲解", description="对指定红色文化知识点进行详细讲解，从背景、内容、历史意义等多维度展开。")
def explain_concept(req: AskRequest):
    pipe = get_pipeline()
    try: return pipe.explain(req.question)
    except Exception as e: raise HTTPException(500, detail=str(e))


# ===== 在线测验 =====

@app.post("/api/quiz/generate", tags=["在线测验"], operation_id="生成题目",
    summary="生成测验题目", description="根据指定主题，从知识库中检索相关内容，自动生成测验题目。")
def quiz_generate(
    topic: str = Form("红色文化", description="测验主题关键词"),
    num: int = Form(5, description="题目数量", ge=1, le=20),
    qtype: str = Form("single", description="题目类型：single=单选题 / multi=多选题 / short=简答题"),
):
    pipe = get_pipeline()
    try: return pipe.quiz_generate(topic, num, qtype)
    except Exception as e: raise HTTPException(500, detail=str(e))


@app.post("/api/quiz/answer", tags=["在线测验"], operation_id="提交答案",
    summary="提交单题答案", description="逐题提交作答结果，支持单选、多选和简答。")
def quiz_answer(req: QuizAnswerRequest):
    pipe = get_pipeline()
    try:
        pipe.quiz_answer(req.question_id, req.answer)
        return {"status": "ok", "message": "答案已提交"}
    except Exception as e: raise HTTPException(500, detail=str(e))


@app.post("/api/quiz/grade", tags=["在线测验"], operation_id="自动判分",
    summary="自动判分", description="对所有已提交答案进行自动批改，返回得分、正确率、逐题解析。")
def quiz_grade():
    pipe = get_pipeline()
    try: return pipe.quiz_grade()
    except Exception as e: raise HTTPException(500, detail=str(e))


@app.post("/api/quiz/reset", tags=["在线测验"], operation_id="重置测验",
    summary="重置测验", description="清除当前测验的所有题目和作答记录，开始新一轮。")
def quiz_reset():
    pipe = get_pipeline()
    pipe.quiz_reset()
    return {"status": "ok", "message": "测验已重置"}


@app.get("/api/quiz/wrong", tags=["在线测验"], operation_id="获取错题",
    summary="获取错题", description="返回上一轮测验中的所有错题及详细解析。")
def quiz_wrong():
    pipe = get_pipeline()
    return pipe.quiz_get_wrong()


# ===== 语音播报 =====

@app.post("/api/narrate", tags=["语音播报"], operation_id="语音播报",
    summary="文字转语音", description="将文本合成为语音播报文件，适合红色故事朗读场景。使用 Edge TTS 引擎。")
def narrate(req: NarrateRequest):
    pipe = get_pipeline()
    try: return pipe.narrate(req.text, req.title)
    except Exception as e: raise HTTPException(500, detail=str(e))


# ===== 多媒体资源 =====

@app.get("/api/media", tags=["多媒体资源"], operation_id="浏览媒体",
    summary="浏览媒体资源", description="分类型浏览图片、视频、音频资源，可按标签筛选。")
def media_list(
    type: Optional[str] = Query(None, alias="type", description="资源类型：images / videos / audio。不填返回全部"),
    tag: Optional[str] = Query(None, description="按标签筛选"),
):
    pipe = get_pipeline()
    return pipe.media_list(type, tag)


@app.post("/api/media/upload", tags=["多媒体资源"], operation_id="上传媒体",
    summary="上传媒体资源", description="上传图片、视频或音频文件，支持添加标题和标签分类。")
async def media_upload(
    file: UploadFile = File(..., description="媒体文件（图片/视频/音频）"),
    title: str = Form("", description="资源标题"),
    tags: str = Form("", description="标签，多个用逗号分隔"),
):
    pipe = get_pipeline()
    try:
        ext = Path(file.filename).suffix
        file_id = uuid.uuid4().hex[:12]
        save_path = uploads_dir / f"{file_id}{ext}"
        content = await file.read()
        save_path.write_bytes(content)
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        entry = pipe.media_add(str(save_path), title or file.filename, tag_list)
        return {"status": "success", "message": "上传成功", "entry": entry}
    except Exception as e: raise HTTPException(500, detail=str(e))


@app.delete("/api/media/{file_id}", tags=["多媒体资源"], operation_id="删除媒体",
    summary="删除媒体资源", description="根据资源 ID 删除指定媒体文件。")
def media_delete(file_id: str = FPath(..., description="媒体资源的唯一标识 ID")):
    pipe = get_pipeline()
    ok = pipe.media_delete(file_id)
    if not ok: raise HTTPException(404, detail="资源不存在")
    return {"status": "deleted", "message": "已删除"}


@app.put("/api/media/{file_id}", tags=["多媒体资源"], operation_id="更新媒体信息",
    summary="更新媒体信息", description="修改媒体资源的标题和标签。")
def media_update(file_id: str = FPath(..., description="媒体资源的唯一标识 ID"), req: MediaUpdateRequest = ...):
    pipe = get_pipeline()
    ok = pipe.media_update(file_id, req.title, req.tags)
    if not ok: raise HTTPException(404, detail="资源不存在")
    return {"status": "updated", "message": "已更新"}


# ===== 知识库管理 =====

@app.post("/api/docs/upload", tags=["知识库管理"], operation_id="上传知识文档",
    summary="上传知识文档", description="上传文本知识文档到知识库。支持 .txt / .md / .pdf / .docx 格式。")
async def docs_upload(file: UploadFile = File(..., description="知识文档文件（txt/md/pdf/docx）")):
    try:
        save_path = config.DATA_DIR / file.filename
        content = await file.read()
        save_path.write_bytes(content)
        return {"status": "success", "message": f"{file.filename} 上传成功", "filename": file.filename}
    except Exception as e: raise HTTPException(500, detail=str(e))


@app.get("/api/docs", tags=["知识库管理"], operation_id="列出文档",
    summary="列出知识文档", description="查看当前知识库中的所有文档文件及大小。")
def docs_list():
    pipe = get_pipeline()
    files = pipe.loader.list_files()
    return [{"name": f.name, "size": f.stat().st_size} for f in files]


@app.delete("/api/docs/{filename}", tags=["知识库管理"], operation_id="删除文档",
    summary="删除知识文档", description="从知识库中移除指定文档文件。")
def docs_delete(filename: str = FPath(..., description="要删除的文档文件名")):
    file_path = config.DATA_DIR / filename
    if not file_path.exists(): raise HTTPException(404, detail="文档不存在")
    file_path.unlink()
    return {"status": "deleted", "message": f"{filename} 已删除"}


# ===== 系统管理 =====

@app.post("/api/build", tags=["系统管理"], operation_id="重建索引",
    summary="重建向量索引", description="清空现有向量库，重新加载全部知识文档并构建向量索引。")
def build_index():
    pipe = get_pipeline()
    try:
        pipe.build_index(clear_first=True)
        return {"status": "success", "message": "索引构建完成", "document_count": pipe.vector_store.document_count()}
    except Exception as e: raise HTTPException(500, detail=str(e))


@app.get("/api/status", tags=["系统管理"], operation_id="系统状态",
    summary="系统状态", description="查看系统运行状态：文档数、媒体资源数、向量库条目数、模型信息。")
def system_status():
    pipe = get_pipeline()
    return pipe.status()


@app.get("/api/search", tags=["系统管理"], operation_id="文档检索",
    summary="文档检索", description="在知识库中语义检索相关内容，返回匹配的文档片段。")
def search_docs(
    query: str = Query(..., description="检索关键词"),
    top_k: int = Query(5, description="返回结果数量", ge=1, le=50),
):
    pipe = get_pipeline()
    return {"query": query, "results": pipe.search_docs(query, top_k)}
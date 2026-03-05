from fastapi import FastAPI, HTTPException, Body, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from loguru import logger
import uuid
import time
import sys

# 导入新模块
from database import engine, SessionLocal, get_db
from models_db import Base, Profile, ChatLog, KnowledgeBaseFile
from models import UserProfile, ChatRequest, DailyNutritionTarget
from utils import calculate_nutrition_needs
from llm_service import LLMService

# 初始化数据库表
Base.metadata.create_all(bind=engine)

# 配置日志记录器
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/app.log", rotation="10 MB", level="DEBUG")

app = FastAPI(title="Smart Elderly Nutritionist API", version="2.0")

# 配置 CORS (跨域资源共享)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    logger.info(f"Request {request_id} started: {request.method} {request.url}")
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Request {request_id} completed: {response.status_code} in {process_time:.4f}s")
    return response

# 数据库依赖
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

llm = LLMService()

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart Elderly Nutritionist API v2.0 (DB Enabled)"}

# --- 画像管理 ---

@app.post("/profile")
async def create_profile(profile: UserProfile, db: Session = Depends(get_db_session)):
    profile_id = str(uuid.uuid4())
    
    # 保存到数据库
    db_profile = Profile(
        id=profile_id,
        age=profile.age,
        gender=profile.gender,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        activity_level=profile.activity_level,
        health_conditions=profile.health_conditions,
        allergies=profile.allergies,
        preferences=profile.preferences
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    
    targets = calculate_nutrition_needs(profile)
    logger.info(f"Created profile {profile_id}")
    return {"profile_id": profile_id, "nutrition_targets": targets}

@app.get("/profile/{profile_id}")
async def get_profile(profile_id: str, db: Session = Depends(get_db_session)):
    db_profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # 将 DB 模型转换回 Pydantic
    return UserProfile(
        age=db_profile.age,
        gender=db_profile.gender,
        height_cm=db_profile.height_cm,
        weight_kg=db_profile.weight_kg,
        activity_level=db_profile.activity_level,
        health_conditions=db_profile.health_conditions,
        allergies=db_profile.allergies,
        preferences=db_profile.preferences
    )

# --- 聊天与工具 ---

@app.post("/calculate_nutrition")
async def calculate_nutrition_endpoint(profile: UserProfile):
    """
    Dify 工具端点：无状态计算
    """
    targets = calculate_nutrition_needs(profile)
    return {
        "targets": targets,
        "summary": f"每日热量 {targets.calories}kcal, 蛋白 {targets.protein_g}g, 钠 < {targets.sodium_mg}mg"
    }

@app.post("/chat/{profile_id}")
async def chat(profile_id: str, request: ChatRequest, db: Session = Depends(get_db_session)):
    """
    旧版聊天端点 (用于 Streamlit) - 现已支持持久化
    """
    db_profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # 重建 Pydantic 模型
    user_profile = UserProfile(
        age=db_profile.age,
        gender=db_profile.gender,
        height_cm=db_profile.height_cm,
        weight_kg=db_profile.weight_kg,
        activity_level=db_profile.activity_level,
        health_conditions=db_profile.health_conditions,
        allergies=db_profile.allergies,
        preferences=db_profile.preferences
    )
    
    # 如果请求中缺失，手动添加画像 (兼容旧客户端)
    request.user_profile = user_profile
    
    nutrition_targets = calculate_nutrition_needs(user_profile)
    
    # 记录用户消息
    db.add(ChatLog(profile_id=profile_id, role="user", content=request.message))
    db.commit()

    # 生成回复
    response = llm.get_response(request, str(nutrition_targets.model_dump()))
    
    # 记录助手消息
    db.add(ChatLog(profile_id=profile_id, role="assistant", content=response))
    db.commit()
    
    return {"reply": response}

# --- 知识库管理 ---

@app.get("/knowledge/status")
async def kb_status(db: Session = Depends(get_db_session)):
    files = db.query(KnowledgeBaseFile).all()
    return {"files": [{"filename": f.filename, "status": f.status, "last_synced": f.last_synced_at} for f in files]}

@app.post("/knowledge/trigger_sync")
async def trigger_kb_sync():
    """
    触发后台 RAG 管道以同步本地文档到 Dify
    """
    from rag_pipeline.dify_sync import run_sync_process
    # 在真实应用中，请使用 BackgroundTasks
    try:
        result = run_sync_process()
        return {"status": "success", "details": result}
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/dify_tool.json")
def get_dify_tool_schema():
    """
    Dify 工具的 OpenAPI Schema
    """
    openapi_schema = app.openapi()
    paths = {
        "/calculate_nutrition": openapi_schema["paths"]["/calculate_nutrition"]
    }
    schemas = {}
    for name in ["UserProfile", "DailyNutritionTarget", "ValidationError", "HTTPValidationError"]:
        if name in openapi_schema["components"]["schemas"]:
            schemas[name] = openapi_schema["components"]["schemas"][name]
            
    return {
        "openapi": "3.0.1",
        "info": {
            "title": "Smart Elderly Nutritionist Tool",
            "description": "用于计算老年人每日营养目标与膳食限制的工具",
            "version": "2.0.0"
        },
        "servers": [{"url": "http://host.docker.internal:8002"}],
        "paths": paths,
        "components": {"schemas": schemas}
    }

# --- System Management ---
import os
import signal
import threading

@app.post("/system/shutdown")
async def shutdown_app():
    """
    Shutdown the server programmatically
    """
    logger.info("Received shutdown signal from frontend.")
    
    def kill():
        time.sleep(1)
        logger.info("Shutting down process...")
        os.kill(os.getpid(), signal.SIGTERM)
        
    threading.Thread(target=kill).start()
    return {"status": "shutting_down"}

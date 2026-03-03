from fastapi import FastAPI, HTTPException, Body, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from loguru import logger
import uuid
import time
import sys

# Import new modules
from database import engine, SessionLocal, get_db
from models_db import Base, Profile, ChatLog, KnowledgeBaseFile
from models import UserProfile, ChatRequest, DailyNutritionTarget
from utils import calculate_nutrition_needs
from llm_service import LLMService

# Initialize DB tables
Base.metadata.create_all(bind=engine)

# Configure Logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/app.log", rotation="10 MB", level="DEBUG")

app = FastAPI(title="Smart Elderly Nutritionist API", version="2.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for Logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    logger.info(f"Request {request_id} started: {request.method} {request.url}")
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Request {request_id} completed: {response.status_code} in {process_time:.4f}s")
    return response

# Dependency
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

# --- Profile Management ---

@app.post("/profile")
async def create_profile(profile: UserProfile, db: Session = Depends(get_db_session)):
    profile_id = str(uuid.uuid4())
    
    # Save to DB
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
    
    # Convert DB model back to Pydantic
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

# --- Chat & Tools ---

@app.post("/calculate_nutrition")
async def calculate_nutrition_endpoint(profile: UserProfile):
    """
    Dify Tool Endpoint: Stateless calculation
    """
    targets = calculate_nutrition_needs(profile)
    return {
        "targets": targets,
        "summary": f"每日热量 {targets.calories}kcal, 蛋白 {targets.protein_g}g, 钠 < {targets.sodium_mg}mg"
    }

@app.post("/chat/{profile_id}")
async def chat(profile_id: str, request: ChatRequest, db: Session = Depends(get_db_session)):
    """
    Legacy Chat Endpoint (for Streamlit) - Now with persistence
    """
    db_profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Reconstruct Pydantic model
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
    
    # Add profile to request manually if missing (for legacy client compatibility)
    request.user_profile = user_profile
    
    nutrition_targets = calculate_nutrition_needs(user_profile)
    
    # Log User Message
    db.add(ChatLog(profile_id=profile_id, role="user", content=request.message))
    db.commit()

    # Generate Response
    response = llm.get_response(request, str(nutrition_targets.model_dump()))
    
    # Log Assistant Message
    db.add(ChatLog(profile_id=profile_id, role="assistant", content=response))
    db.commit()
    
    return {"reply": response}

# --- Knowledge Base Management ---

@app.get("/knowledge/status")
async def kb_status(db: Session = Depends(get_db_session)):
    files = db.query(KnowledgeBaseFile).all()
    return {"files": [{"filename": f.filename, "status": f.status, "last_synced": f.last_synced_at} for f in files]}

@app.post("/knowledge/trigger_sync")
async def trigger_kb_sync():
    """
    Trigger the background RAG pipeline to sync local docs to Dify
    """
    from rag_pipeline.dify_sync import run_sync_process
    # In a real app, use BackgroundTasks
    try:
        result = run_sync_process()
        return {"status": "success", "details": result}
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/dify_tool.json")
def get_dify_tool_schema():
    """
    OpenAPI Schema for Dify Tool
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

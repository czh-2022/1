from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.sql import func
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=True) # Optional link to User
    age = Column(Integer)
    gender = Column(String)
    height_cm = Column(Float)
    weight_kg = Column(Float)
    activity_level = Column(String)
    health_conditions = Column(JSON) # Store as JSON list
    allergies = Column(JSON) # Store as JSON list
    preferences = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(String, index=True)
    role = Column(String) # user, assistant, system
    content = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    meta_info = Column(JSON, nullable=True) # Store intent, tool calls, etc.

class KnowledgeBaseFile(Base):
    __tablename__ = "kb_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True)
    status = Column(String) # uploaded, synced, error
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    dify_document_id = Column(String, nullable=True)

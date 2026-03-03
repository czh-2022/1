from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal

class UserProfile(BaseModel):
    age: int = Field(..., description="Age in years")
    gender: Literal["male", "female"] = Field(..., description="Gender")
    height_cm: float = Field(..., description="Height in cm")
    weight_kg: float = Field(..., description="Weight in kg")
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"] = Field(..., description="Activity level")
    health_conditions: List[str] = Field(default_factory=list, description="List of health conditions (e.g., 'diabetes', 'hypertension')")
    allergies: List[str] = Field(default_factory=list, description="List of allergies")
    preferences: str = Field(default="", description="Dietary preferences or restrictions")

class DailyNutritionTarget(BaseModel):
    calories: int
    protein_g: float
    fat_g: float
    carbs_g: float
    sodium_mg: Optional[float] = None
    sugar_g: Optional[float] = None
    fiber_g: Optional[float] = None

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = Field(default_factory=list)
    user_profile: Optional[UserProfile] = None  # Optional for API, populated by backend

class ChatResponse(BaseModel):
    reply: str
    suggested_actions: List[str] = Field(default_factory=list)

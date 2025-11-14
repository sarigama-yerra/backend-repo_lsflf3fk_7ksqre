"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Core user profile (optional for future expansion)
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    is_active: bool = Field(True, description="Active status")

# Track IELTS scores over time
class Userscore(BaseModel):
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    module: str = Field(..., description="IELTS module: Listening/Reading/Writing/Speaking/Overall")
    score: float = Field(..., ge=0, le=9, description="Band score 0-9, can be .5 increments")
    note: Optional[str] = Field(None, description="Optional note, e.g., test center or attempt")
    date: Optional[datetime] = Field(default_factory=datetime.utcnow, description="When this score was recorded")

# Save writing submissions and evaluations
class Writingsample(BaseModel):
    user_id: Optional[str] = None
    task_type: str = Field(..., description="Task1 or Task2")
    prompt: Optional[str] = None
    content: str = Field(..., description="Student's writing")
    estimated_band: Optional[float] = None
    feedback: Optional[str] = None
    date: Optional[datetime] = Field(default_factory=datetime.utcnow)

# Simple reminders
class Reminder(BaseModel):
    user_id: Optional[str] = None
    title: str
    due_date: datetime
    category: Optional[str] = Field(None, description="reading/listening/writing/speaking/general")
    done: bool = False

# Weakness profile snapshots
class Weaknessprofile(BaseModel):
    user_id: Optional[str] = None
    weaknesses: List[str] = []
    suggestions: List[str] = []
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

# Note: The Flames database viewer will automatically read these schemas via /schema endpoint (if implemented)
# and help you manage collections named after lowercase model names:
# userscore -> scores, writingsample -> writing samples, reminder -> reminders, etc.

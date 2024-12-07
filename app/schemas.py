from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TaskCreate(BaseModel):
    title: str
    description: str
    due_date: datetime
    status: str


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  
    due_date: Optional[datetime] = None  # Changed from str to datetime



class TaskResponse(BaseModel):
    id: str  # 'id' should be a string
    title: str
    description: str
    due_date: datetime
    status: str
    created_at: datetime

    class Config:
        orm_mode = True  # Allow ORM-style objects to be serialized properly
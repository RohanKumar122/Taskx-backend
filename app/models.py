from pydantic import BaseModel, Field, validator
from bson import ObjectId
from enum import Enum
from datetime import datetime
from typing import Optional


class User(BaseModel):
    email: str
    password: str

    class Config:
        from_attributes = True


class UserInDB(User):
    id: str 


class TaskStatus(str, Enum):
    todo = "To Do"
    in_progress = "In Progress"
    done = "Done"


class TaskBase(BaseModel):
    title: str
    description: str
    status: TaskStatus
    due_date: datetime


class TaskCreate(BaseModel):
    title: str
    description: str
    due_date: datetime
    status: str


class Task(TaskBase):
    id: str = Field(..., alias="_id")  

    @validator('id', pre=True)
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    class Config:
        from_attributes = True  


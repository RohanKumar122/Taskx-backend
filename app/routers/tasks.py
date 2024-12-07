from fastapi import APIRouter, HTTPException, Depends
from app.database import db, tasks_collection
from app.schemas import TaskCreate, TaskUpdate, TaskResponse
from bson import ObjectId
from datetime import datetime, timedelta
from typing import Optional
from app.auth import get_current_user
from pymongo import ASCENDING

router = APIRouter(prefix="/tasks", tags=["Tasks"])

def validate_object_id(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid task ID")
    return ObjectId(id)

def convert_utc_to_ist(utc_time: datetime) -> datetime:
    return utc_time + timedelta(hours=5, minutes=30)

@router.get("/", response_model=list[TaskResponse])
async def get_tasks(status: Optional[str] = None, current_user: str = Depends(get_current_user)):
    try:
        query = {"user": current_user}
        if status:
            query["status"] = status

        tasks = list(tasks_collection.find(query).sort("due_date", ASCENDING))
        

        for task in tasks:
            task["id"] = str(task["_id"])  
            del task["_id"]  

            if "created_at" in task and isinstance(task["created_at"], datetime):
                task["created_at"] = convert_utc_to_ist(task["created_at"]) 

        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tasks: {str(e)}")
    

@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, current_user: str = Depends(get_current_user)):
    task_dict = task.dict()
    task_dict["user"] = current_user 
    task_dict["created_at"] = datetime.utcnow() 


    result = tasks_collection.insert_one(task_dict)
    task_dict["_id"] = str(result.inserted_id)  

    return TaskResponse(id=task_dict["_id"], **task_dict)

@router.get("/order-by-due-date", response_model=list[TaskResponse])
async def get_tasks_ordered_by_due_date(current_user: str = Depends(get_current_user)):
    tasks = list(tasks_collection.find({"user": current_user}).sort("due_date", ASCENDING))
    for task in tasks:
        task["_id"] = str(task["_id"]) 
    return tasks

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task: TaskUpdate, current_user: str = Depends(get_current_user)):
    task_id = validate_object_id(task_id)

    update_data = {k: v for k, v in task.dict(exclude_unset=True).items()}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")

    result = tasks_collection.find_one_and_update(
        {"_id": task_id, "user": current_user},  
        {"$set": update_data},
        return_document=True,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Task not found")

    result["_id"] = str(result["_id"])  
    return TaskResponse(id=result["_id"], **result)

@router.delete("/{task_id}")
async def delete_task(task_id: str, current_user: str = Depends(get_current_user)):
    task_id = validate_object_id(task_id)
    result = tasks_collection.delete_one({"_id": task_id, "user": current_user})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}

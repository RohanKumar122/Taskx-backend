from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.routers import tasks
from app.auth import create_access_token, authenticate_user
from app.models import User
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv  # Import dotenv
from fastapi import HTTPException, Body
from app.database import db, user_collection,pwd_context

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the port from the .env file, default to 8800 if not set
PORT = int(os.getenv("PORT", 8800))

@app.get("/")
async def root():
    return {"message": "FastAPI app is running!"}

# Token route for login
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # user = authenticate_user(form_data.username, form_data.password)
    user = user_collection.find_one({"username": form_data.username})
    if not user or not pwd_context.verify(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register")
async def register(username: str = Body(...), password: str = Body(...)):
    # Check if user exists
    if user_collection.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash the password
    hashed_password = pwd_context.hash(password)
    
    # Save user to database
    user_collection.insert_one({"username": username, "password": hashed_password})
    return {"message": "User registered successfully"}

app.include_router(tasks.router)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Render assigns the PORT environment variable
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from datetime import datetime, timedelta
import os
from pydantic import BaseModel
from passlib.context import CryptContext
from app.database import db  # Assuming you have a database connection already
from fastapi import FastAPI

app = FastAPI()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # Hashing passwords

# User registration schema
class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    username: str

class UserInDB(User):
    password: str

# Function to hash password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Function to verify hashed password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Function to get user from database (assuming MongoDB or other DB)
def get_user(db, username: str) -> UserInDB | None:
    user_dict = db.users.find_one({"username": username})
    if user_dict:
        return UserInDB(**user_dict)
    return None

# Function to authenticate user
def authenticate_user(db, username: str, password: str) -> UserInDB | None:
    user = get_user(db, username)
    if user and verify_password(password, user.password):
        return user
    return None

# Function to create JWT token
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Function to get current user from the JWT token

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Decode the token using the secret key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials"
            )
        
        # Fetch the user from the database
        user = db.users.find_one({"username": username})
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return user  # or a User object if necessary
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=403,
            detail="Invalid token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}"
        )
# Register a new user
@app.post("/register")
async def register(user: UserCreate):
    # Check if the username already exists
    if db.users.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash the password before saving it to the database
    hashed_password = hash_password(user.password)
    
    # Save the user to the database
    db.users.insert_one({"username": user.username, "password": hashed_password})
    return {"message": "User registered successfully"}

# Token route (to get the JWT token after login)
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Protected route (requires authentication)
@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Welcome, {current_user.username}!"}

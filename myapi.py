# HTTP Requests
# GET
# POST
# PUT
# DELETE

from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Boolean, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, Session
from typing import List, Optional
import bcrypt
import jwt

app = FastAPI(title="Integration with SQL")
# Security Config
SECRET_KEY = "asdf"
ALGORITHM = "HS256"
TOKEN_EXPIRES = 30


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database Ssetup
engine = create_engine("sqlite:///users.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Base Pydantic Models
class User(Base):
    __tablename__="users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_pwd: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

Base.metadata.create_all(engine)

# Pydantic models
class UserCreate(BaseModel):
    name: str
    email: str
    role: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None   


# Security functions
def verify_pwd(plain_pwd: str, hashed_pwd: str) -> bool:
    return bcrypt.checkpw(plain_pwd.encode("utf-8"), hashed_pwd.encode("utf-8"))


def get_pwd_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str =  payload["sub"]
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not verify credentials.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return TokenData(email=email)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

## Create database
get_db()


# Auth Dependencies
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    token_data = verify_token(token)
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user
    
def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inactive User",
        )
    return current_user


# Auth endpoints
@app.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists.")

    hashed_password = get_pwd_hash(user.password)
    db_user = User ( 
        name = user.name,
        email = user.email,
        role = user.role,
        hashed_pwd = hashed_password,

    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_pwd(form_data.password, user.hashed_pwd):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

    access_token_expires = timedelta(minutes=TOKEN_EXPIRES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hello, World"}

@app.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.get("/verify-token")
def verify_token_endpoint(current_user: User = Depends(get_current_active_user)):
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email":current_user.email,
            "role": current_user.role
        }

    }
# Create User
@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # Check if user exists
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=409, detail="User already exists.")

    # Create new user
    hashed_password = get_pwd_hash(user.password)
    new_user = User(
            name = user.name,
            email = user.email,
            role = user.role,
            hashed_pwd = hashed_password
        )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Read User
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

# Update User
@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, updated_user: UserCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User does not exist.")

    db_user.name = updated_user.name 
    db_user.email = updated_user.email
    db_user.role = updated_user.role

    db.commit()
    db.refresh(db_user)
    return db_user


# Delete User
@app.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, current_user: User = Depends(get_current_active_user), db: Session= Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User does not exist.")

    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can't delete own account")

    db.delete(db_user)
    db.commit()
    return db_user

# Get all Users
@app.get("/users/", response_model=List[UserResponse])
def get_all_users(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return db.query(User).all()

# Search User
@app.get("/users/search/", response_model=UserResponse)
def search_user(email: Optional[str] = None, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")

    return db_user
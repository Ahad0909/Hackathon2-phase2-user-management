# backend/main.py

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# --------------------------
# Database setup
# --------------------------
DATABASE_URL = "postgresql://neondb_owner:npg_C8krd6jOpLiD@ep-billowing-rain-aivmasnp-pooler.c-4.us-east-1.aws.neon.tech/neondb"

engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"},
    echo=True,
    pool_pre_ping=True
)

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=True, autocommit=False)

# --------------------------
# Database model
# --------------------------
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

# --------------------------
# Pydantic models
# --------------------------
class User(BaseModel):
    name: str
    email: str

class UserResponse(User):
    id: int

# --------------------------
# FastAPI app
# --------------------------
app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # frontend localhost ko allow karna
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB session dependency
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# --------------------------
# Routes
# --------------------------

@app.get("/users", response_model=List[UserResponse])
def get_users(session: Session = Depends(get_session)):
    return session.query(UserDB).all()

@app.post("/users", response_model=UserResponse)
def add_user(user: User, session: Session = Depends(get_session)):
    db_user = UserDB(name=user.name, email=user.email)
    try:
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: User, session: Session = Depends(get_session)):
    db_user = session.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.name = user.name
    db_user.email = user.email
    try:
        session.commit()
        session.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/users/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session)):
    db_user = session.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        session.delete(db_user)
        session.commit()
        return {"detail": "User deleted"}
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


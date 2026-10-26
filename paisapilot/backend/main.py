from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import engine, get_db
from models import User
from schemas import UserCreate, UserLogin, UserOut, TokenOut
from auth import hash_password, verify_password, create_token, get_current_user

app = FastAPI(title="PaisaPilot")

@app.get("/health")
def health():
    return {"status": "OK"}

@app.get("/db-check")
def db_check():
    with engine.connect() as conn:
        conn.execute(text("SELECT COUNT(*) FROM categories"))
    return {"database": "connected"}

@app.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    user = User(name=data.name, email=data.email,
                password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/login", response_model=TokenOut)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"access_token": create_token(user.id), "token_type": "bearer"}

@app.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
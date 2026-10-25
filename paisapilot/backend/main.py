from fastapi import FastAPI
from sqlalchemy import text
from database import engine

app = FastAPI(title="PaisaPilot")

@app.get("/health")
def health():
    return {"status": "OK"}

@app.get("/db-check")
def db_check():
    with engine.connect() as conn:
        conn.execute(text("SELECT COUNT(*) FROM categories"))
    return {"database": "connected"}
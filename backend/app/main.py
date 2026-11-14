from fastapi import FastAPI

from .db import init_db

app = FastAPI(title="ORBIT Health", version="0.1.0")


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

"""FastAPI application for Commodity Sentiment Index."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import sentiment
from storage.db import init_db

app = FastAPI(title="Commodity Sentiment Index API", version="2.0.0")


@app.on_event("startup")
def startup():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:22265",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sentiment.router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok", "service": "commodity-sentiment-index"}


@app.get("/api/health")
def health():
    return {"status": "ok"}

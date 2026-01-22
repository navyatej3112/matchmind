from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import ingest, analytics, ml

app = FastAPI(title="MatchMind API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(analytics.router, prefix="", tags=["analytics"])
app.include_router(ml.router, prefix="", tags=["ml"])


@app.get("/")
def root():
    return {"message": "MatchMind API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


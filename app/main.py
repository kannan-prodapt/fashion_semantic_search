# app/main.py
from fastapi import FastAPI
from app.api.v1.search_routes import router as search_router

app = FastAPI(title="Fashion Search API")

app.include_router(search_router, prefix="/v1")

# Optional: health check
@app.get("/health")
def health():
    return {"status": "ok"}

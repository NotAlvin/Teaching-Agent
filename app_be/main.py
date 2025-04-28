# type: ignore

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app_be.api import content
from app_be.database.db import init_db

app = FastAPI(title="Linear Algebra Learning Platform API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(content.router, prefix="/api/content", tags=["content"])


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to Linear Algebra Learning Platform API"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from routes import analyze
from routes import auth as auth_router
from services.database import init_db

app = FastAPI(
    title="FiltreLAB AI Backend",
    description="Backend AI Analysis Engine for FiltreLAB",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(auth_router.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
async def root():
    return {"message": "FiltreLAB AI Engine is running. Visit /docs for API documentation."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

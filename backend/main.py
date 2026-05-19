import sys

# Windows: force UTF-8 console output so Turkish characters in logs don't crash.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

import asyncio

# Windows: Playwright launches the browser as a subprocess, which only works on
# the ProactorEventLoop. This must run before uvicorn creates the event loop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from dotenv import load_dotenv

load_dotenv()

from routes import analyze
from routes import auth as auth_router
from routes import user_features
from routes import reviews as reviews_router
from routes import cross_platform as cross_platform_router
from routes import pseudo_comprehend as pseudo_comprehend_router
from routes import psychology as psychology_router
from services.database import init_db

app = FastAPI(
    title="FiltreLAB AI Backend",
    description="Backend AI Analysis Engine for FiltreLAB",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(auth_router.router)
app.include_router(user_features.router)
app.include_router(reviews_router.router)
app.include_router(cross_platform_router.router)
app.include_router(pseudo_comprehend_router.router)
app.include_router(psychology_router.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
async def root():
    return {"message": "FiltreLAB AI Engine is running. Visit /docs for API documentation."}


if __name__ == "__main__":
    import uvicorn
    # reload=False so this process keeps the ProactorEventLoop policy set above.
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)

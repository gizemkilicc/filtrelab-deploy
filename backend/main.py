from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import analyze

app = FastAPI(
    title="FiltreLAB AI Backend",
    description="Backend AI Analysis Engine for FiltreLAB",
    version="1.0.0"
)

# Enable CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)

@app.get("/")
async def root():
    return {"message": "FiltreLAB AI Engine is running. Visit /docs for API documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

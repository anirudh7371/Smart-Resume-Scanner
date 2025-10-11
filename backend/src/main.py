import uvicorn
from fastapi import FastAPI
from src.api.endpoints import router as api_router

app = FastAPI(title="Smart Resume Screener")

app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {"status": "ok", "app": "Smart Resume Screener"}

@app.get("/upload_resume", methods=["POST"])
def upload_resume():
    pass

@app.get("/analyze_match", methods=["POST"])
def analyze_match():
    pass

@app.get("/get_recommendations", methods=["GET"])
def get_recommendations():
    pass

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)

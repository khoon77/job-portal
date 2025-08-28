from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from Vercel!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/jobs/list")
def get_jobs():
    return {"success": True, "data": []}

handler = app
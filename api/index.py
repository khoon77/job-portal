# api/index.py
"""
Vercel용 FastAPI 엔트리포인트
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

try:
    from main import app
    handler = app
    print("[Vercel] FastAPI app loaded successfully")
except Exception as e:
    print(f"[Vercel] Failed to load FastAPI app: {e}")
    
    # fallback: 간단한 FastAPI 앱 생성
    from fastapi import FastAPI
    
    fallback_app = FastAPI()
    
    @fallback_app.get("/")
    async def root():
        return {"message": "Fallback API is running", "error": str(e)}
    
    @fallback_app.get("/health")
    async def health():
        return {"status": "fallback", "error": str(e)}
    
    handler = fallback_app
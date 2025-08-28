# config.py
"""
프로젝트 설정 파일
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 설정
NARAITEO_API_KEY = os.getenv("NARAITEO_API_KEY", "1bmDITdGFoaDTSrbT6Uyz8bFdlIL3nydHgRu0xQtXO8SiHlCrOJKv+JNSythF12BiijhVB3qE96/4Jxr70zUNg==")
NARAITEO_BASE_URL = os.getenv("NARAITEO_BASE_URL", "http://openapi.mpm.go.kr/openapi/service/RetrievePblinsttEmpmnInfoService")

# Firebase 설정
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "job-portal-c9d7f-firebase-adminsdk-fbsvc-b0f6caa11d.json")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "job-portal-c9d7f")

# 서버 설정
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8001))
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"

# 데이터 설정
DEFAULT_JOBS_PER_PAGE = int(os.getenv("DEFAULT_JOBS_PER_PAGE", 20))
MAX_JOBS_PER_REQUEST = int(os.getenv("MAX_JOBS_PER_REQUEST", 100))
API_REQUEST_TIMEOUT = int(os.getenv("API_REQUEST_TIMEOUT", 15))

# CORS 설정
ALLOWED_ORIGINS_STRING = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173,http://127.0.0.1:8001,*")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_STRING.split(",")]
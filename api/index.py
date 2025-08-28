# api/index.py
"""
Vercel용 FastAPI 엔트리포인트
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

# Vercel이 인식할 수 있도록 handler 함수 노출
handler = app
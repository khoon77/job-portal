# api/index.py
"""
Vercel용 FastAPI 엔트리포인트 - 단순화된 버전
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from typing import Optional

# FastAPI 앱 생성
app = FastAPI(
    title="나라일터 채용정보 API",
    description="공공기관 채용공고 정보를 제공하는 API 서버",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 테스트 데이터
SAMPLE_JOBS = [
    {
        "idx": "264754",
        "title": "2025년도 일반임기제공무원 경력채용 시험 안내",
        "dept_name": "기획재정부",
        "reg_date": "20250125",
        "end_date": "20250208",
        "read_count": 1234,
        "grade": "7급",
        "work_region": "서울특별시",
        "etc_info": "N||N"
    },
    {
        "idx": "264755",
        "title": "2025년 상반기 청년인턴 채용공고",
        "dept_name": "문화체육관광부",
        "reg_date": "20250120",
        "end_date": "20250205",
        "read_count": 987,
        "grade": "인턴",
        "work_region": "경기도",
        "etc_info": "청년우대"
    }
]

@app.get("/")
async def root():
    """메인 페이지"""
    return {
        "message": "나라일터 채용정보 API",
        "status": "running",
        "version": "1.0.0",
        "environment": "vercel"
    }

@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "environment": "vercel",
        "message": "서버가 정상적으로 작동 중입니다."
    }

@app.get("/debug")
async def debug_info():
    """디버그 정보"""
    import sys
    return {
        "python_version": sys.version,
        "environment_vars": {
            "VERCEL": os.getenv("VERCEL", "Not Set"),
            "VERCEL_ENV": os.getenv("VERCEL_ENV", "Not Set"),
            "FIREBASE_PROJECT_ID": os.getenv("FIREBASE_PROJECT_ID", "Not Set"),
        },
        "platform": sys.platform,
        "executable": sys.executable
    }

@app.get("/api/jobs/list")
async def get_jobs_list(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None
):
    """채용공고 목록 조회"""
    try:
        jobs = SAMPLE_JOBS.copy()
        
        # 검색 필터링
        if search:
            search_lower = search.lower()
            jobs = [
                job for job in jobs
                if search_lower in job.get('title', '').lower() 
                or search_lower in job.get('dept_name', '').lower()
            ]
        
        return {
            "success": True,
            "data": jobs,
            "total": len(jobs),
            "page": page,
            "limit": limit,
            "search": search,
            "source": "vercel_static_data",
            "message": "Vercel 환경에서 정적 테스트 데이터를 제공합니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/stats")
async def get_jobs_statistics():
    """채용공고 통계 정보"""
    try:
        return {
            "success": True,
            "data": {
                "total_jobs": len(SAMPLE_JOBS),
                "urgent_jobs": 1,
                "recent_jobs": 2,
                "total_departments": len(set(job['dept_name'] for job in SAMPLE_JOBS)),
                "sample_jobs": SAMPLE_JOBS[:2]
            },
            "source": "vercel_static_data",
            "message": "Vercel 환경에서 정적 통계 데이터를 제공합니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/detail/{idx}")
async def get_job_detail(idx: str):
    """채용공고 상세 정보"""
    try:
        job = next((j for j in SAMPLE_JOBS if j['idx'] == idx), None)
        if not job:
            job = {
                "idx": idx,
                "title": "테스트 채용공고",
                "dept_name": "테스트 기관",
                "reg_date": "20250125",
                "end_date": "20250208",
                "read_count": 100,
                "grade": "미확인",
                "work_region": "미확인",
                "etc_info": "N||N"
            }
        
        return {
            "success": True,
            "data": job,
            "source": "vercel_static_data"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/content/{idx}")
async def get_job_content(idx: str):
    """채용공고 상세 내용"""
    try:
        content = """
            <div style="text-align: center; padding: 40px; color: #6b7280; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">
                <div style="font-size: 24px; margin-bottom: 15px;">📄</div>
                <h4 style="color: #374151; margin-bottom: 10px;">Vercel 환경에서 실행 중</h4>
                <p style="margin-bottom: 8px; font-size: 13px;">현재 Vercel 서버리스 함수에서 실행되고 있습니다.</p>
                <p style="color: #9ca3af; font-size: 12px;">실제 채용공고 내용은 나라일터 원문에서 확인하세요.</p>
            </div>
        """
        
        return {
            "success": True,
            "data": {
                "contents": content,
                "links": [
                    {
                        "title": "나라일터 채용공고 원문 보기",
                        "url": f"https://www.gojobs.go.kr/apmView.do?empmnsn={idx}",
                        "type": "원문"
                    }
                ]
            },
            "source": "vercel_static_data"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/files/{idx}")
async def get_job_files(idx: str):
    """채용공고 첨부파일"""
    try:
        return {
            "success": True,
            "data": [],
            "source": "vercel_static_data",
            "message": "Vercel 환경에서는 첨부파일을 제공하지 않습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Vercel handler
handler = app
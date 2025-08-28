# main_with_firebase.py
"""
Firebase 연동 FastAPI 서버
- 정적 데이터 대신 Firebase에서 실제 데이터 조회
- 확정된 UI와 완벽 호환
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
from config import ALLOWED_ORIGINS
from firebase_optimized import OptimizedFirebaseService

# FastAPI 앱 생성
app = FastAPI(
    title="나라일터 채용정보 API (Firebase 연동)",
    description="Firebase 기반 채용정보 서비스",
    version="2.0.0"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firebase 서비스 인스턴스
firebase_service = OptimizedFirebaseService()

@app.get("/")
async def root():
    """메인 페이지 - HTML 파일 서빙"""
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    
    return HTMLResponse(content="""
    <html>
        <head>
            <title>나라일터 채용정보 (Firebase)</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                .container { max-width: 800px; margin: 0 auto; }
                .header { background: #667eea; color: white; padding: 20px; border-radius: 8px; text-align: center; }
                .status { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔥 나라일터 채용정보 (Firebase 연동)</h1>
                    <p>실시간 Firebase 데이터 서비스</p>
                </div>
                
                <div class="status">
                    <h2>📊 시스템 상태</h2>
                    <ul>
                        <li><strong>GET /api/jobs/list</strong> - Firebase 채용공고 목록</li>
                        <li><strong>GET /api/jobs/detail/{idx}</strong> - 채용공고 상세 정보</li>
                        <li><strong>GET /api/jobs/stats</strong> - 실시간 통계</li>
                        <li><strong>GET /docs</strong> - API 문서</li>
                    </ul>
                </div>
            </div>
        </body>
    </html>
    """)

@app.get("/api/jobs/list")
async def get_jobs_list(page: int = 1, limit: int = 20, search: str = ""):
    """Firebase에서 채용공고 목록 조회"""
    
    try:
        print(f"[Firebase API] 채용공고 목록 조회 - 페이지: {page}, 한도: {limit}")
        
        # Firebase에서 데이터 조회
        all_jobs = firebase_service.get_jobs_minimal(limit=100)  # 충분히 가져와서 필터링
        
        # 검색어 필터링
        if search:
            filtered_jobs = []
            search_lower = search.lower()
            for job in all_jobs:
                title = job.get('title', '').lower()
                dept = job.get('dept_name', '').lower()
                if search_lower in title or search_lower in dept:
                    filtered_jobs.append(job)
            jobs = filtered_jobs
        else:
            jobs = all_jobs
        
        # 페이지네이션
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        page_jobs = jobs[start_idx:end_idx]
        
        # UI 호환성을 위한 데이터 변환
        converted_jobs = []
        for job in page_jobs:
            # Firebase 데이터를 기존 UI 형식으로 변환
            converted_job = {
                "idx": str(job.get("idx", job.get("id", ""))),
                "title": job.get("title", ""),
                "dept_name": job.get("dept_name", ""),
                "reg_date": job.get("reg_date", ""),
                "end_date": job.get("end_date", ""),
                "read_count": job.get("read_count", 0),
                "grade": job.get("grade", "미확인"),
                "work_region": job.get("work_region", "미확인"),
                "etc_info": job.get("etc_info", "일반채용"),
                "contents": job.get("contents", ""),
                "files": job.get("files", [])
            }
            converted_jobs.append(converted_job)
        
        print(f"[Firebase] ✅ {len(converted_jobs)}개 채용공고 반환")
        
        return {
            "success": True,
            "data": converted_jobs,
            "total": len(jobs),
            "page": page,
            "limit": limit,
            "search": search,
            "source": "firebase_realtime",
            "message": "Firebase에서 실시간 데이터 조회"
        }
        
    except Exception as e:
        print(f"[오류] Firebase 목록 조회 실패: {e}")
        # 폴백: 빈 배열 반환
        return {
            "success": False,
            "data": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "search": search,
            "source": "firebase_error",
            "message": f"데이터 조회 실패: {str(e)}"
        }

@app.get("/api/jobs/detail/{idx}")
async def get_job_detail(idx: str):
    """Firebase에서 채용공고 상세정보 조회"""
    
    try:
        print(f"[Firebase API] 채용공고 상세 조회 - ID: {idx}")
        
        # Firebase에서 특정 문서 조회
        job = firebase_service.get_job_by_id(idx)
        
        if not job:
            print(f"[Firebase] ⚠️ 공고 {idx} 없음")
            raise HTTPException(status_code=404, detail="채용공고를 찾을 수 없습니다")
        
        # UI 호환성을 위한 데이터 변환
        converted_job = {
            "idx": str(job.get("idx", job.get("id", ""))),
            "title": job.get("title", ""),
            "dept_name": job.get("dept_name", ""),
            "reg_date": job.get("reg_date", ""),
            "end_date": job.get("end_date", ""),
            "read_count": job.get("read_count", 0),
            "grade": job.get("grade", "미확인"),
            "work_region": job.get("work_region", "미확인"),
            "etc_info": job.get("etc_info", "일반채용")
        }
        
        print(f"[Firebase] ✅ 공고 {idx} 상세정보 반환")
        
        return {
            "success": True,
            "data": converted_job,
            "source": "firebase_realtime",
            "message": "Firebase에서 실시간 상세정보 조회"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[오류] Firebase 상세 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"상세 정보 조회 실패: {str(e)}")

@app.get("/api/jobs/content/{idx}")
async def get_job_content(idx: str):
    """채용공고 상세 내용 조회"""
    
    try:
        print(f"[Firebase API] 채용공고 내용 조회 - ID: {idx}")
        
        job = firebase_service.get_job_by_id(idx)
        
        if not job:
            return {
                "success": False,
                "data": {"contents": "상세 내용을 찾을 수 없습니다."},
                "message": "해당 공고를 찾을 수 없습니다"
            }
        
        contents = job.get("contents", "상세 내용이 없습니다.")
        
        return {
            "success": True,
            "data": {"contents": contents},
            "source": "firebase_realtime",
            "message": "Firebase에서 상세 내용 조회"
        }
        
    except Exception as e:
        print(f"[오류] Firebase 내용 조회 실패: {e}")
        return {
            "success": False,
            "data": {"contents": "내용을 가져올 수 없습니다."},
            "message": f"내용 조회 실패: {str(e)}"
        }

@app.get("/api/jobs/files/{idx}")
async def get_job_files(idx: str):
    """채용공고 첨부파일 목록 조회"""
    
    try:
        print(f"[Firebase API] 첨부파일 조회 - ID: {idx}")
        
        job = firebase_service.get_job_by_id(idx)
        
        if not job:
            return {
                "success": False,
                "data": [],
                "message": "해당 공고를 찾을 수 없습니다"
            }
        
        files = job.get("files", [])
        
        print(f"[Firebase] ✅ {len(files)}개 첨부파일 반환")
        
        return {
            "success": True,
            "data": files,
            "source": "firebase_realtime",
            "message": f"{len(files)}개 첨부파일 조회"
        }
        
    except Exception as e:
        print(f"[오류] Firebase 파일 조회 실패: {e}")
        return {
            "success": False,
            "data": [],
            "message": f"파일 조회 실패: {str(e)}"
        }

@app.get("/api/jobs/stats")
async def get_job_statistics():
    """Firebase 기반 실시간 통계 조회"""
    
    try:
        print("[Firebase API] 통계 조회")
        
        # Firebase에서 통계 조회
        stats = firebase_service.get_stats_optimized()
        
        # 기본값 설정
        if not stats:
            stats = {
                "total_jobs": 0,
                "urgent_jobs": 0,
                "new_jobs": 0,
                "total_departments": 0
            }
        
        print("[Firebase] ✅ 통계 정보 반환")
        
        return {
            "success": True,
            "data": stats,
            "source": "firebase_realtime",
            "message": "Firebase 실시간 통계"
        }
        
    except Exception as e:
        print(f"[오류] Firebase 통계 조회 실패: {e}")
        # 폴백 통계
        return {
            "success": True,
            "data": {
                "total_jobs": 0,
                "urgent_jobs": 0,
                "new_jobs": 0,
                "total_departments": 0,
                "last_updated": "Unknown"
            },
            "source": "firebase_fallback",
            "message": "통계 조회 실패, 기본값 반환"
        }

@app.get("/health")
async def health_check():
    """시스템 상태 확인"""
    firebase_status = "connected" if firebase_service.db else "disconnected"
    
    return {
        "status": "healthy",
        "firebase": firebase_status,
        "service": "firebase_realtime",
        "message": "Firebase 연동 서비스 정상 작동"
    }

if __name__ == "__main__":
    import uvicorn
    print("🔥 Firebase 연동 서버 시작...")
    print("📊 Firebase 상태:", "✅ 연결됨" if firebase_service.db else "❌ 연결 실패")
    uvicorn.run(app, host="127.0.0.1", port=8000)
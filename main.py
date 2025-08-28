# main.py
"""
FastAPI 메인 애플리케이션
나라일터 채용정보 API 서버
"""

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
from typing import List, Dict, Any, Optional

# Vercel 환경에서의 import 문제 해결
try:
    from naraiteo_api import NaraiteoAPI
    from config import *
    print("[Main] Modules imported successfully")
except ImportError as e:
    print(f"[Main] Import error: {e}")
    # 기본값 설정
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 8000
    DEBUG_MODE = False
    DEFAULT_JOBS_PER_PAGE = 20
    ALLOWED_ORIGINS = ["*"]
    
    # NaraiteoAPI 모킹
    class NaraiteoAPI:
        def get_job_list(self, *args, **kwargs):
            return []
        def get_job_detail(self, *args, **kwargs):
            return None
        def get_job_files(self, *args, **kwargs):
            return []

# FastAPI 앱 생성
app = FastAPI(
    title="나라일터 채용정보 API",
    description="공공기관 채용공고 정보를 제공하는 API 서버",
    version="1.0.0"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 나라일터 API 인스턴스
naraiteo_api = NaraiteoAPI()

# Firebase 서비스 인스턴스
try:
    from firebase_service import FirebaseJobService
    firebase_service = FirebaseJobService()
    print("[Main] Firebase service initialized")
except Exception as e:
    print(f"[Main] Firebase service initialization failed: {e}")
    # Firebase 서비스 모킹
    class FirebaseJobService:
        def __init__(self):
            self.db = None
        def get_jobs(self, *args, **kwargs):
            return []
        def get_job_by_id(self, *args, **kwargs):
            return None
        def get_statistics(self, *args, **kwargs):
            return {}
    
    firebase_service = FirebaseJobService()

@app.get("/")
async def root():
    """메인 페이지 - HTML 파일이 있으면 서빙"""
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    
    return HTMLResponse(content="""
    <html>
        <head>
            <title>나라일터 채용정보</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                .container { max-width: 800px; margin: 0 auto; }
                .header { background: #4834d4; color: white; padding: 20px; border-radius: 8px; text-align: center; }
                .api-info { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>나라일터 채용정보 API</h1>
                    <p>공공기관 채용공고 정보 서비스</p>
                </div>
                
                <div class="api-info">
                    <h2>API 엔드포인트</h2>
                    <ul>
                        <li><strong>GET /api/jobs/list</strong> - 채용공고 목록 조회</li>
                        <li><strong>GET /api/jobs/detail/{idx}</strong> - 채용공고 상세 조회</li>
                        <li><strong>GET /health</strong> - 서버 상태 확인</li>
                        <li><strong>GET /docs</strong> - API 문서 (Swagger)</li>
                    </ul>
                </div>
            </div>
        </body>
    </html>
    """)

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
        "python_path": sys.path[:5],  # 처음 5개만
        "environment_vars": {
            "VERCEL": os.getenv("VERCEL"),
            "VERCEL_ENV": os.getenv("VERCEL_ENV"),
            "FIREBASE_PROJECT_ID": os.getenv("FIREBASE_PROJECT_ID", "Not Set"),
        },
        "firebase_db_status": "connected" if firebase_service.db else "disconnected"
    }

@app.get("/api/jobs/list")
@app.get("/api/recruitment/enhanced")  # 브라우저 캐시 호환성을 위한 추가 엔드포인트
async def get_jobs_list(
    page: int = 1,
    limit: int = DEFAULT_JOBS_PER_PAGE,
    numOfRows: int = None,  # 다른 파라미터명 지원
    search: Optional[str] = None,
    refresh: bool = False  # 강제 새로고침 파라미터
):
    """채용공고 목록 조회 - Firebase 우선, 정적 데이터 백업"""
    try:
        print(f"[API 요청] 채용공고 목록 - 페이지: {page}, 제한: {limit}")
        
        # Firebase에서 데이터 먼저 시도
        if firebase_service.db:
            try:
                print("[데이터 소스] Firebase에서 데이터 조회 중...")
                offset = (page - 1) * limit
                
                if search:
                    # 검색이 있으면 검색 함수 사용
                    firebase_jobs = firebase_service.search_jobs(keyword=search)
                else:
                    # 일반 목록 조회
                    firebase_jobs = firebase_service.get_jobs(limit=limit*2, offset=offset)  # 여유롭게 가져오기
                
                if firebase_jobs and len(firebase_jobs) > 0:
                    print(f"[Firebase] {len(firebase_jobs)}건의 데이터 조회 성공")
                    
                    return {
                        "success": True,
                        "data": firebase_jobs,
                        "total": len(firebase_jobs),
                        "page": page,
                        "limit": limit,
                        "search": search,
                        "source": "firebase",
                        "message": f"Firebase에서 {len(firebase_jobs)}건의 채용공고를 가져왔습니다."
                    }
                else:
                    print("[Firebase] 저장된 데이터가 없습니다. 정적 데이터를 사용합니다.")
                    
            except Exception as fb_error:
                print(f"[Firebase] 조회 실패: {fb_error}")
        
        # Firebase 실패시 또는 데이터가 없으면 정적 데이터 사용
        print("[데이터 소스] 정적 테스트 데이터 사용")
        sample_jobs = [
            {"idx": "264754", "title": "2025년도 일반임기제공무원 경력채용 시험 안내", "dept_name": "기획재정부", "reg_date": "20250125", "end_date": "20250208", "read_count": 1234, "grade": "7급", "work_region": "서울특별시", "etc_info": "N||N"},
            {"idx": "264755", "title": "2025년 상반기 청년인턴 채용공고", "dept_name": "문화체육관광부", "reg_date": "20250120", "end_date": "20250205", "read_count": 987, "grade": "인턴", "work_region": "경기도", "etc_info": "청년우대"},
            {"idx": "264756", "title": "국가직 9급 공무원 공개채용", "dept_name": "행정안전부", "reg_date": "20250118", "end_date": "20250201", "read_count": 2567, "grade": "9급", "work_region": "전국", "etc_info": "N||N"},
            {"idx": "264757", "title": "연구원 채용공고 (박사급)", "dept_name": "한국과학기술연구원", "reg_date": "20250115", "end_date": "20250130", "read_count": 543, "grade": "연구원", "work_region": "대전광역시", "etc_info": "N||N"},
            {"idx": "264758", "title": "기술직 공무원 채용 (토목직렬)", "dept_name": "국토교통부", "reg_date": "20250112", "end_date": "20250128", "read_count": 876, "grade": "8급", "work_region": "세종특별자치시", "etc_info": "N||N"},
            {"idx": "264759", "title": "환경직 공무원 채용공고", "dept_name": "환경부", "reg_date": "20250110", "end_date": "20250125", "read_count": 654, "grade": "9급", "work_region": "서울특별시", "etc_info": "N||N"},
            {"idx": "264760", "title": "보건직 공무원 신규채용", "dept_name": "보건복지부", "reg_date": "20250108", "end_date": "20250122", "read_count": 432, "grade": "8급", "work_region": "부산광역시", "etc_info": "N||N"},
            {"idx": "264761", "title": "교육행정직 공무원 채용", "dept_name": "교육부", "reg_date": "20250105", "end_date": "20250220", "read_count": 1876, "grade": "6급", "work_region": "대구광역시", "etc_info": "N||N"},
            {"idx": "264762", "title": "외교관 후보자 선발시험", "dept_name": "외교부", "reg_date": "20250103", "end_date": "20250215", "read_count": 3421, "grade": "5급", "work_region": "서울특별시", "etc_info": "N||N"},
            {"idx": "264763", "title": "농업연구사 채용공고", "dept_name": "농촌진흥청", "reg_date": "20250102", "end_date": "20250210", "read_count": 789, "grade": "연구사", "work_region": "전라북도", "etc_info": "N||N"},
            {"idx": "264764", "title": "전산직 공무원 경력채용", "dept_name": "과학기술정보통신부", "reg_date": "20250101", "end_date": "20250131", "read_count": 2134, "grade": "7급", "work_region": "경기도", "etc_info": "N||N"},
            {"idx": "264765", "title": "사회복지직 공무원 채용", "dept_name": "보건복지부", "reg_date": "20241230", "end_date": "20250115", "read_count": 1543, "grade": "9급", "work_region": "인천광역시", "etc_info": "N||N"},
            {"idx": "264766", "title": "문화재수리기능자 채용공고", "dept_name": "문화재청", "reg_date": "20241228", "end_date": "20250110", "read_count": 234, "grade": "기능직", "work_region": "경상북도", "etc_info": "N||N"},
            {"idx": "264767", "title": "산림청 임업연구사 신규채용", "dept_name": "산림청", "reg_date": "20241225", "end_date": "20250105", "read_count": 567, "grade": "연구사", "work_region": "강원도", "etc_info": "N||N"},
            {"idx": "264768", "title": "해양수산부 어업지도선 선원 채용", "dept_name": "해양수산부", "reg_date": "20241223", "end_date": "20250103", "read_count": 345, "grade": "기능직", "work_region": "부산광역시", "etc_info": "N||N"}
        ]
        
        # 검색어 필터링
        if search:
            filtered_jobs = []
            search_lower = search.lower()
            for job in sample_jobs:
                title = job.get('title', '').lower()
                dept = job.get('dept_name', '').lower()
                if search_lower in title or search_lower in dept:
                    filtered_jobs.append(job)
            jobs = filtered_jobs
        else:
            jobs = sample_jobs
        
        return {
            "success": True,
            "data": jobs,
            "total": len(jobs),
            "page": page,
            "limit": limit,
            "search": search,
            "source": "static_fallback",
            "message": "Firebase에 저장된 데이터가 없어 정적 테스트 데이터를 제공합니다."
        }
        
    except Exception as e:
        print(f"[오류] 채용공고 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"채용공고 목록 조회 실패: {str(e)}"
        )

@app.get("/api/jobs/detail/{idx}")
async def get_job_detail(idx: str):
    """채용공고 기본 정보 조회 - Firebase 우선, 정적 데이터 백업"""
    try:
        print(f"[API 요청] 채용공고 기본 정보 - ID: {idx}")
        
        # Firebase에서 데이터 먼저 시도
        if firebase_service.db:
            try:
                print(f"[데이터 소스] Firebase에서 ID {idx} 조회 중...")
                firebase_job = firebase_service.get_job_by_id(idx)
                
                if firebase_job:
                    print(f"[Firebase] ID {idx} 데이터 조회 성공")
                    return {
                        "success": True,
                        "data": firebase_job,
                        "source": "firebase"
                    }
                else:
                    print(f"[Firebase] ID {idx}에 해당하는 데이터가 없습니다.")
                    
            except Exception as fb_error:
                print(f"[Firebase] 조회 실패: {fb_error}")
        
        # Firebase 실패시 또는 데이터가 없으면 정적 데이터 사용
        print(f"[데이터 소스] 정적 테스트 데이터 사용 - ID: {idx}")
        static_jobs = {
            "264754": {
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
            "264755": {
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
        }
        
        if idx in static_jobs:
            return {
                "success": True,
                "data": static_jobs[idx],
                "source": "static_data"
            }
        
        # 기본 데이터 제공 (ID가 매핑에 없는 경우)
        return {
            "success": True,
            "data": {
                "idx": idx,
                "title": "테스트 채용공고",
                "dept_name": "테스트 기관",
                "reg_date": "20250125",
                "end_date": "20250208",
                "read_count": 100,
                "grade": "미확인",
                "work_region": "미확인",
                "etc_info": "N||N"
            },
            "source": "static_fallback"
        }
        
    except Exception as e:
        print(f"[오류] 채용공고 기본 정보 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"채용공고 기본 정보 조회 실패: {str(e)}"
        )

@app.get("/api/jobs/content/{idx}")
async def get_job_content(idx: str, response: Response):
    """채용공고 상세 내용 조회 - 실제 나라일터 API 데이터"""
    try:
        print(f"[API 요청] 채용공고 상세 내용 - ID: {idx}")
        
        from datetime import datetime
        
        # 브라우저 캐시 방지 헤더 설정
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        # 나라일터 API에서 실제 상세 내용 조회
        try:
            print(f"[데이터 소스] 나라일터 API에서 상세 내용 조회 중...")
            detail_data = naraiteo_api.get_job_detail(idx)
            
            if detail_data and detail_data.get('contents'):
                actual_content = detail_data['contents']
                print(f"[나라일터 API] 상세 내용 조회 성공 (길이: {len(actual_content)})")
                
                # 실제 관련 링크 - 나라일터 원문만 제공 (다른 링크는 API에서 제공 안함)
                actual_links = [
                    {
                        "title": "나라일터 채용공고 원문 보기",
                        "url": f"https://www.gojobs.go.kr/apmView.do?empmnsn={idx}&selMenuNo=400&menuNo=401&upperMenuNo=",
                        "type": "원문"
                    }
                ]
                
                return {
                    "success": True,
                    "data": {
                        "contents": actual_content,
                        "links": actual_links
                    },
                    "source": "naraiteo_api",
                    "message": f"나라일터 API에서 상세 내용을 가져왔습니다.",
                    "cache_buster": datetime.now().isoformat()
                }
                
            else:
                print(f"[나라일터 API] ID {idx}에 상세 내용이 없습니다.")
                # 내용이 없는 경우 안내 메시지 표시
                fallback_content = f"""
                    <div style="text-align: center; padding: 40px; color: #6b7280; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">
                        <div style="font-size: 24px; margin-bottom: 15px;">📄</div>
                        <h4 style="color: #374151; margin-bottom: 10px;">상세 내용 없음</h4>
                        <p style="margin-bottom: 8px; font-size: 13px;">이 채용공고의 상세 내용을 가져올 수 없습니다.</p>
                        <p style="color: #9ca3af; font-size: 12px;">나라일터 원문을 확인해주세요.</p>
                    </div>
                """
                
                return {
                    "success": True,
                    "data": {
                        "contents": fallback_content,
                        "links": [
                            {
                                "title": "나라일터 채용공고 원문 보기",
                                "url": f"https://www.gojobs.go.kr/apmView.do?empmnsn={idx}&selMenuNo=400&menuNo=401&upperMenuNo=",
                                "type": "원문"
                            }
                        ]
                    },
                    "source": "naraiteo_api_fallback",
                    "message": "상세 내용이 없습니다.",
                    "cache_buster": datetime.now().isoformat()
                }
                
        except Exception as api_error:
            print(f"[나라일터 API] 상세 내용 조회 실패: {api_error}")
            
            # API 실패시 안내 메시지 표시
            error_content = f"""
                <div style="text-align: center; padding: 40px; color: #ef4444; background: #fef2f2; border-radius: 8px; border: 1px solid #fecaca;">
                    <div style="font-size: 24px; margin-bottom: 15px;">⚠️</div>
                    <h4 style="color: #dc2626; margin-bottom: 10px;">상세 내용 로딩 실패</h4>
                    <p style="margin-bottom: 8px; font-size: 13px;">상세 내용을 가져오는 중 오류가 발생했습니다.</p>
                    <p style="color: #9ca3af; font-size: 12px;">나라일터 원문에서 직접 확인해주세요.</p>
                </div>
            """
            
            return {
                "success": True,
                "data": {
                    "contents": error_content,
                    "links": [
                        {
                            "title": "나라일터 채용공고 원문 보기",
                            "url": f"https://www.gojobs.go.kr/apmView.do?empmnsn={idx}&selMenuNo=400&menuNo=401&upperMenuNo=",
                            "type": "원문"
                        }
                    ]
                },
                "source": "api_error_fallback",
                "message": f"상세 내용 조회 실패: {str(api_error)}",
                "cache_buster": datetime.now().isoformat()
            }
        
    except Exception as e:
        print(f"[오류] 상세 내용 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"상세 내용 조회 실패: {str(e)}"
        )

@app.get("/api/jobs/files/{idx}")
async def get_job_files(idx: str):
    """채용공고 첨부파일 조회 - 실제 나라일터 API 데이터"""
    try:
        print(f"[API 요청] 채용공고 첨부파일 - ID: {idx}")
        
        # 나라일터 API에서 실제 첨부파일 조회
        try:
            print(f"[데이터 소스] 나라일터 API에서 첨부파일 조회 중...")
            actual_files = naraiteo_api.get_job_files(idx)
            
            if actual_files:
                print(f"[나라일터 API] {len(actual_files)}개 첨부파일 조회 성공")
                return {
                    "success": True,
                    "data": actual_files,
                    "source": "naraiteo_api",
                    "message": f"나라일터 API에서 {len(actual_files)}개 첨부파일을 가져왔습니다."
                }
            else:
                print(f"[나라일터 API] ID {idx}에 첨부파일이 없습니다.")
                return {
                    "success": True,
                    "data": [],
                    "source": "naraiteo_api",
                    "message": "첨부파일이 없습니다."
                }
                
        except Exception as api_error:
            print(f"[나라일터 API] 첨부파일 조회 실패: {api_error}")
            # API 실패시 빈 배열 반환
            return {
                "success": True,
                "data": [],
                "source": "api_fallback",
                "message": "첨부파일 조회 중 오류가 발생했습니다."
            }
        
    except Exception as e:
        print(f"[오류] 첨부파일 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"첨부파일 조회 실패: {str(e)}"
        )

@app.get("/api/jobs/stats")
async def get_jobs_statistics():
    """채용공고 통계 정보 - Firebase 우선 조회"""
    try:
        print("[API 요청] 통계 정보 조회")
        
        # Firebase에서 통계 먼저 시도
        if firebase_service.db:
            try:
                print("[데이터 소스] Firebase에서 통계 조회 중...")
                firebase_stats = firebase_service.get_statistics()
                
                if firebase_stats:
                    print("[Firebase] 통계 조회 성공")
                    return {
                        "success": True,
                        "data": firebase_stats,
                        "source": "firebase",
                        "message": f"Firebase에서 통계 정보를 가져왔습니다."
                    }
                else:
                    print("[Firebase] 통계 데이터가 없습니다.")
                    
            except Exception as fb_error:
                print(f"[Firebase] 통계 조회 실패: {fb_error}")
        
        # Firebase 실패시 정적 데이터 사용
        print("[통계] 정적 테스트 데이터 제공")
        
        return {
            "success": True,
            "data": {
                "total_jobs": 127,
                "urgent_jobs": 8,
                "recent_jobs": 23,
                "total_departments": 15,
                "sample_jobs": [
                    {
                        "idx": "264754",
                        "title": "2025년도 일반임기제공무원 경력채용 시험 안내",
                        "dept_name": "기획재정부"
                    },
                    {
                        "idx": "264755", 
                        "title": "2025년 상반기 청년인턴 채용공고",
                        "dept_name": "문화체육관광부"
                    }
                ]
            },
            "source": "static_fallback",
            "message": "Firebase에 저장된 데이터가 없어 정적 테스트 데이터를 제공합니다."
        }
        
    except Exception as e:
        print(f"[오류] 통계 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"통계 조회 실패: {str(e)}"
        )

@app.post("/api/jobs/sync")
async def sync_jobs_data(days: int = 30, batch_size: int = 50):
    """30일치 채용공고 데이터 동기화 및 Firebase 저장"""
    try:
        print(f"[동기화] {days}일치 데이터 수집 시작")
        
        if not firebase_service.db:
            raise HTTPException(status_code=500, detail="Firebase 연결이 필요합니다")
        
        total_collected = 0
        page = 1
        max_pages = 10  # 최대 페이지 수 제한 (API 호출 제한)
        
        collected_jobs = []
        
        # 여러 페이지에서 데이터 수집
        while page <= max_pages:
            try:
                print(f"[동기화] 페이지 {page} 수집 중...")
                jobs = naraiteo_api.get_job_list(page_no=page, num_of_rows=batch_size)
                
                if not jobs:
                    print(f"[동기화] 페이지 {page}에서 데이터 없음, 중단")
                    break
                
                collected_jobs.extend(jobs)
                total_collected += len(jobs)
                page += 1
                
                # 너무 많은 API 호출 방지 (최대 500건)
                if total_collected >= 500:
                    print(f"[동기화] 최대 수집량 도달 ({total_collected}건), 중단")
                    break
                    
            except Exception as api_error:
                print(f"[동기화] 페이지 {page} 수집 실패: {api_error}")
                break
        
        # Firebase에 일괄 저장
        if collected_jobs:
            success = firebase_service.save_jobs(collected_jobs)
            if success:
                print(f"[동기화] 총 {total_collected}건 Firebase에 저장 완료")
            else:
                raise HTTPException(status_code=500, detail="Firebase 저장 실패")
        
        # 만료된 데이터 정리
        from job_manager import JobManager
        try:
            manager = JobManager()
            cleanup_result = manager.cleanup_expired_jobs()
            cleanup_count = cleanup_result.get("deleted", 0)
        except Exception as cleanup_error:
            print(f"[동기화] 정리 실패: {cleanup_error}")
            cleanup_count = 0
        
        return {
            "success": True,
            "message": f"{days}일치 데이터 동기화 완료",
            "collected": total_collected,
            "pages_processed": page - 1,
            "cleaned_up": cleanup_count,
            "final_data_count": total_collected - cleanup_count
        }
        
    except Exception as e:
        print(f"[오류] 데이터 동기화 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"데이터 동기화 실패: {str(e)}"
        )

@app.post("/api/jobs/cleanup")
async def cleanup_old_jobs():
    """30일 지난 게시글 정리 (마감일이 지난 경우만)"""
    try:
        print("[API 요청] 게시글 정리")
        
        # job_manager를 사용해서 정리 (Firebase 연결이 있는 경우)
        try:
            from job_manager import JobManager
            manager = JobManager()
            result = manager.cleanup_expired_jobs()
            return {
                "success": result["success"],
                "message": result["message"],
                "details": result
            }
        except Exception as cleanup_error:
            print(f"[주의] Firebase 정리 실패: {cleanup_error}")
            # Firebase 없이도 기본 응답
            return {
                "success": True,
                "message": "게시글 정리는 Firebase 연결이 필요합니다.",
                "note": "현재는 실시간 API에서 최신 데이터를 직접 가져오고 있습니다."
            }
        
    except Exception as e:
        print(f"[오류] 게시글 정리 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"게시글 정리 실패: {str(e)}"
        )

# 개발 서버 실행용
if __name__ == "__main__":
    import uvicorn
    
    print("나라일터 채용정보 API 서버 시작")
    print(f"주소: http://{SERVER_HOST}:{SERVER_PORT}")
    print("API 문서: http://{SERVER_HOST}:{SERVER_PORT}/docs")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=DEBUG_MODE
    )
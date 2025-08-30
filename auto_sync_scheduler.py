"""
GitHub Actions용 자동 동기화 스크립트
5분마다 실행되어 신규 게시글만 Firebase에 저장
"""
import os
import sys
import json
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
from naraiteo_api import NaraiteoAPI
import time

def initialize_firebase():
    """Firebase 초기화"""
    if not firebase_admin._apps:
        # GitHub Actions에서는 환경변수로 인증키 전달
        if os.getenv('GITHUB_ACTIONS'):
            # GitHub Secrets에서 Firebase 인증 정보 가져오기
            firebase_config = {
                "type": "service_account",
                "project_id": os.getenv('FIREBASE_PROJECT_ID'),
                "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
                "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
                "client_id": os.getenv('FIREBASE_CLIENT_ID'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL')
            }
            
            cred = credentials.Certificate(firebase_config)
        else:
            # 로컬 실행시에는 파일 사용
            cred = credentials.Certificate("job-portal-c9d7f-firebase-adminsdk-fbsvc-b0f6caa11d.json")
        
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

def get_existing_job_ids(db):
    """Firebase에서 기존 게시글 ID 목록 조회"""
    try:
        docs = db.collection('jobs').stream()
        existing_ids = set()
        for doc in docs:
            existing_ids.add(doc.id)
        return existing_ids
    except Exception as e:
        print(f"[ERROR] 기존 게시글 ID 조회 오류: {e}")
        return set()

def sync_new_jobs():
    """신규 게시글만 동기화"""
    print("=" * 70)
    print("[AUTO SYNC] 신규 게시글 자동 동기화 시작")
    print(f"[TIME] 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        # Firebase 초기화
        db = initialize_firebase()
        
        # 기존 게시글 ID 목록 가져오기
        print("[INFO] 기존 게시글 ID 목록 조회...")
        existing_ids = get_existing_job_ids(db)
        print(f"   기존 게시글: {len(existing_ids)}개")
        
        # 나라일터 API 초기화
        api = NaraiteoAPI()
        
        # 최신 게시글 목록 조회 (50개)
        print("[API] 나라일터에서 최신 게시글 조회...")
        jobs = api.get_job_list(page_no=1, num_of_rows=50)
        
        if not jobs:
            print("[ERROR] 게시글 조회 실패")
            return
        
        # 신규 게시글 필터링
        new_jobs = []
        for job in jobs:
            if job['idx'] not in existing_ids:
                new_jobs.append(job)
        
        print(f"[NEW] 신규 게시글: {len(new_jobs)}개")
        
        if not new_jobs:
            print("[OK] 신규 게시글이 없습니다. 현행 유지")
            return
        
        # 신규 게시글 상세 정보 수집 및 저장
        saved_count = 0
        for i, job in enumerate(new_jobs, 1):
            try:
                print(f"   [{i}/{len(new_jobs)}] {job['title'][:50]}...")
                
                # 상세 정보 조회
                detail = api.get_job_detail(job['idx'])
                if not detail:
                    continue
                
                # 첨부파일 정보 조회
                files = api.get_job_files(job['idx'])
                
                # Firebase 저장 데이터 구성
                job_data = {
                    **detail,
                    'files': files,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                
                # Firebase에 저장
                db.collection('jobs').document(job['idx']).set(job_data)
                saved_count += 1
                
                # API 호출 간격 (Rate Limiting)
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   [ERROR] 게시글 {job['idx']} 처리 오류: {e}")
                continue
        
        print(f"[SUCCESS] 신규 게시글 {saved_count}개 저장 완료")
        
    except Exception as e:
        print(f"[ERROR] 전체 동기화 오류: {e}")
        sys.exit(1)

def main():
    """메인 함수"""
    try:
        sync_new_jobs()
        print("[COMPLETE] 자동 동기화 완료")
        
    except Exception as e:
        print(f"[FATAL] 치명적 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
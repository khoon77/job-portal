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
        # GitHub Actions와 로컬 모두 JSON 파일 사용
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

def parse_date_string(date_str):
    """날짜 문자열을 datetime 객체로 변환"""
    if not date_str:
        return None
    
    try:
        # YYYY-MM-DD 형식
        if len(date_str) == 10 and '-' in date_str:
            return datetime.strptime(date_str, '%Y-%m-%d')
        
        # YYYY.MM.DD 형식
        elif len(date_str) == 10 and '.' in date_str:
            return datetime.strptime(date_str, '%Y.%m.%d')
        
        # YYYYMMDD 형식
        elif len(date_str) == 8 and date_str.isdigit():
            return datetime.strptime(date_str, '%Y%m%d')
        
        return None
    except:
        return None

def is_job_within_30day_criteria(job_data, today, cutoff_date):
    """
    게시글이 30일 기준에 맞는지 확인
    - reg_date가 30일 이내인 경우: 수집
    - reg_date가 30일 이상이지만 end_date가 아직 안 지난 경우: 수집
    - 그외: 수집 안함
    """
    try:
        # 등록일 파싱 (reg_date 사용)
        reg_date = parse_date_string(job_data.get('reg_date'))
        if not reg_date:
            # 등록일이 없으면 안전하게 수집하지 않음
            return False, "등록일 정보 없음"
        
        # 등록일이 30일 이내인 경우
        if reg_date >= cutoff_date:
            return True, f"등록일 30일 이내 ({reg_date.strftime('%Y-%m-%d')})"
        
        # 등록일이 30일 이상 지난 경우, 마감일 확인
        end_date = parse_date_string(job_data.get('end_date'))
        if end_date and end_date >= today:
            return True, f"마감일 미도과 ({end_date.strftime('%Y-%m-%d')})"
        
        # 둘 다 해당 안됨
        end_date_str = end_date.strftime('%Y-%m-%d') if end_date else "정보없음"
        return False, f"수집 제외 (등록일: {reg_date.strftime('%Y-%m-%d')}, 마감일: {end_date_str})"
        
    except Exception as e:
        return False, f"날짜 파싱 오류: {e}"

def collect_jobs_with_30day_filter(api, today):
    """
    30일 기준 필터링을 적용하여 게시글 수집
    """
    collected_jobs = []
    page_no = 1
    max_pages = 10  # 최대 10페이지까지 확인 (1000개)
    cutoff_date = today - timedelta(days=30)  # 30일 전
    
    print(f"[FILTER] 수집 기준:")
    print(f"   - 기준일: {today.strftime('%Y-%m-%d')}")
    print(f"   - 30일 전: {cutoff_date.strftime('%Y-%m-%d')}")
    print(f"   - 등록일 30일 이내 OR 마감일 미도과 게시글 수집")
    
    while page_no <= max_pages:
        print(f"[API] 페이지 {page_no} 조회 중...")
        
        # 한 페이지당 100개씩 조회
        jobs = api.get_job_list(page_no=page_no, num_of_rows=100)
        
        if not jobs:
            print(f"   페이지 {page_no}: 게시글 없음, 수집 종료")
            break
        
        print(f"   페이지 {page_no}: {len(jobs)}개 게시글 확인")
        
        page_collected = 0
        page_filtered = 0
        
        for job in jobs:
            # 각 게시글에 대해 상세 정보 조회 (등록일/마감일 정보 필요)
            detail = api.get_job_detail(job['idx'])
            if not detail:
                continue
            
            # 필터링 기준 적용
            is_valid, reason = is_job_within_30day_criteria(detail, today, cutoff_date)
            
            if is_valid:
                collected_jobs.append({
                    'basic_info': job,
                    'detail_info': detail,
                    'reason': reason
                })
                page_collected += 1
            else:
                page_filtered += 1
            
            # API 호출 간격 (Rate Limiting)
            time.sleep(0.3)
        
        print(f"   페이지 {page_no} 결과: 수집 {page_collected}개, 제외 {page_filtered}개")
        
        # 다음 페이지로
        page_no += 1
        time.sleep(0.5)  # 페이지 간 간격
    
    print(f"[RESULT] 전체 수집된 게시글: {len(collected_jobs)}개")
    return collected_jobs

def sync_new_jobs():
    """신규 게시글만 동기화"""
    print("=" * 70)
    print("[AUTO SYNC] 30일 기준 필터링 자동 동기화 시작")
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
        
        # 현재 날짜
        today = datetime.now()
        
        # 30일 기준 필터링으로 게시글 수집
        print("[API] 30일 기준 필터링 게시글 수집...")
        collected_jobs = collect_jobs_with_30day_filter(api, today)
        
        if not collected_jobs:
            print("[OK] 30일 기준에 맞는 게시글이 없습니다.")
            return
        
        # 신규 게시글 필터링 (기존 DB와 비교)
        new_jobs = []
        for job_data in collected_jobs:
            job_idx = job_data['basic_info']['idx']
            if job_idx not in existing_ids:
                new_jobs.append(job_data)
        
        print(f"[NEW] 신규 게시글: {len(new_jobs)}개 (전체 수집: {len(collected_jobs)}개)")
        
        if not new_jobs:
            print("[OK] 신규 게시글이 없습니다. 현행 유지")
            return
        
        # 신규 게시글 Firebase 저장
        saved_count = 0
        for i, job_data in enumerate(new_jobs, 1):
            try:
                basic_info = job_data['basic_info']
                detail_info = job_data['detail_info']
                reason = job_data['reason']
                
                print(f"   [{i}/{len(new_jobs)}] {basic_info['title'][:50]}... ({reason})")
                
                # 첨부파일 정보 조회
                files = api.get_job_files(basic_info['idx'])
                
                # Firebase 저장 데이터 구성
                save_data = {
                    **detail_info,
                    'files': files,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'collection_reason': reason  # 수집 이유 기록
                }
                
                # Firebase에 저장
                db.collection('jobs').document(basic_info['idx']).set(save_data)
                saved_count += 1
                
                # API 호출 간격 (Rate Limiting)
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   [ERROR] 게시글 {basic_info['idx']} 처리 오류: {e}")
                continue
        
        print(f"[SUCCESS] 신규 게시글 {saved_count}개 저장 완료")
        
    except Exception as e:
        print(f"[ERROR] 전체 동기화 오류: {e}")
        sys.exit(1)

def main():
    """메인 함수"""
    try:
        sync_new_jobs()
        print("[COMPLETE] 30일 기준 필터링 자동 동기화 완료")
        
    except Exception as e:
        print(f"[FATAL] 치명적 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
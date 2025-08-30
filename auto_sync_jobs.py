"""
자동 데이터 수집 및 정리 시스템
- 나라일터 API에서 최신 채용정보 수집
- 30일 초과 데이터 자동 삭제
- GitHub Actions에서 5분마다 실행
"""
import sys
import io
import firebase_admin
from firebase_admin import credentials, firestore
from naraiteo_api import NaraiteoAPI
from datetime import datetime, timedelta
import time
import os

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Firebase 초기화
if not firebase_admin._apps:
    # GitHub Actions 환경에서는 환경변수에서 credentials 가져오기
    if os.getenv('GITHUB_ACTIONS'):
        import json
        firebase_cred = json.loads(os.getenv('FIREBASE_CREDENTIALS'))
        cred = credentials.Certificate(firebase_cred)
    else:
        # 로컬 환경에서는 파일에서 가져오기
        cred = credentials.Certificate("job-portal-c9d7f-firebase-adminsdk-fbsvc-b0f6caa11d.json")
    
    firebase_admin.initialize_app(cred)

db = firestore.client()

def clean_old_jobs():
    """30일 초과된 게시글 삭제 (마감일이 지난 경우만)"""
    print("\n🧹 오래된 게시글 정리 시작...")
    
    jobs_ref = db.collection('jobs')
    thirty_days_ago = datetime.now() - timedelta(days=30)
    today = datetime.now().strftime('%Y-%m-%d')
    
    deleted_count = 0
    checked_count = 0
    
    # 모든 문서 조회
    docs = jobs_ref.stream()
    
    for doc in docs:
        checked_count += 1
        data = doc.to_dict()
        
        # 등록일과 마감일 확인
        reg_date_str = data.get('reg_date', '')
        end_date_str = data.get('end_date', '')
        
        try:
            # 날짜 문자열을 datetime으로 변환
            if reg_date_str:
                reg_date = datetime.strptime(reg_date_str, '%Y-%m-%d')
                
                # 삭제 조건: 등록일이 30일 이상 지났고, 마감일도 지난 경우
                if reg_date < thirty_days_ago:
                    if end_date_str and end_date_str < today:
                        # 삭제
                        doc.reference.delete()
                        deleted_count += 1
                        print(f"  ❌ 삭제: {data.get('title', 'N/A')[:30]}... (등록: {reg_date_str}, 마감: {end_date_str})")
        except Exception as e:
            print(f"  ⚠️ 날짜 처리 오류 [{doc.id}]: {e}")
    
    print(f"✅ 정리 완료: {checked_count}개 검사, {deleted_count}개 삭제")
    return deleted_count

def check_new_jobs():
    """신규 게시글 확인 및 수집"""
    print("\n🔍 신규 게시글 확인 중...")
    
    api = NaraiteoAPI()
    jobs_ref = db.collection('jobs')
    
    # 최신 10개 게시글 조회
    latest_jobs = api.get_job_list(page_no=1, num_of_rows=10)
    
    new_count = 0
    updated_count = 0
    
    for job in latest_jobs:
        idx = job['idx']
        doc_ref = jobs_ref.document(idx)
        
        # 기존 문서 확인
        doc = doc_ref.get()
        
        if not doc.exists:
            # 신규 게시글 - 상세정보까지 수집
            print(f"  🆕 신규 발견: {job['title'][:40]}...")
            
            try:
                # 상세 정보 가져오기
                detail = api.get_job_detail(idx)
                if detail:
                    job.update(detail)
                
                # 파일 정보 가져오기
                files = api.get_job_files(idx)
                job['files'] = files
                
                # 채용직급 정보 가져오기
                position = api.get_job_position(idx)
                if position and position.get('full_grade'):
                    job['grade'] = position['full_grade']
                
                # Firebase에 저장
                job_data = {
                    **job,
                    'timestamp': firestore.SERVER_TIMESTAMP,
                    'last_updated': datetime.now().isoformat()
                }
                
                doc_ref.set(job_data)
                new_count += 1
                
                # API 호출 제한 고려
                time.sleep(0.5)
                
            except Exception as e:
                print(f"    ❌ 수집 실패: {e}")
        else:
            # 기존 게시글 - 업데이트 필요 확인
            existing_data = doc.to_dict()
            if existing_data.get('title') != job.get('title') or \
               existing_data.get('end_date') != job.get('end_date'):
                # 업데이트 필요
                doc_ref.update({
                    'title': job.get('title'),
                    'end_date': job.get('end_date'),
                    'last_updated': datetime.now().isoformat()
                })
                updated_count += 1
                print(f"  🔄 업데이트: {job['title'][:40]}...")
    
    print(f"✅ 확인 완료: {new_count}개 신규, {updated_count}개 업데이트")
    return new_count, updated_count

def sync_all_if_empty():
    """데이터베이스가 비어있으면 전체 동기화"""
    jobs_ref = db.collection('jobs')
    docs = jobs_ref.limit(1).get()
    
    if len(docs) == 0:
        print("\n⚠️ 데이터베이스가 비어있습니다. 전체 동기화 시작...")
        
        api = NaraiteoAPI()
        jobs = api.get_job_list(page_no=1, num_of_rows=50)  # 최초 50개 가져오기
        
        saved_count = 0
        for job in jobs:
            try:
                idx = job['idx']
                
                # 상세 정보 수집
                detail = api.get_job_detail(idx)
                if detail:
                    job.update(detail)
                
                files = api.get_job_files(idx)
                job['files'] = files
                
                position = api.get_job_position(idx)
                if position and position.get('full_grade'):
                    job['grade'] = position['full_grade']
                
                # 저장
                job_data = {
                    **job,
                    'timestamp': firestore.SERVER_TIMESTAMP,
                    'last_updated': datetime.now().isoformat()
                }
                
                jobs_ref.document(idx).set(job_data)
                saved_count += 1
                
                print(f"  ✅ [{saved_count:2}/50] {job['title'][:40]}...")
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ 실패: {e}")
        
        print(f"✅ 초기 동기화 완료: {saved_count}개 저장")
        return saved_count
    
    return 0

def get_statistics():
    """현재 통계 출력"""
    print("\n📊 현재 데이터베이스 통계")
    print("-" * 50)
    
    jobs_ref = db.collection('jobs')
    all_docs = jobs_ref.stream()
    
    total_count = 0
    active_count = 0
    today = datetime.now().strftime('%Y-%m-%d')
    
    for doc in all_docs:
        total_count += 1
        data = doc.to_dict()
        if data.get('end_date', '') >= today:
            active_count += 1
    
    print(f"  전체 게시글: {total_count}개")
    print(f"  진행중 공고: {active_count}개")
    print(f"  마감된 공고: {total_count - active_count}개")
    
    return total_count, active_count

def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("🚀 나라일터 채용정보 자동 동기화 시스템")
    print(f"⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        # 1. 데이터베이스가 비어있으면 초기 동기화
        initial_sync = sync_all_if_empty()
        
        if initial_sync == 0:
            # 2. 신규 게시글 확인 및 수집
            new_count, updated_count = check_new_jobs()
            
            # 3. 오래된 게시글 정리
            deleted_count = clean_old_jobs()
        
        # 4. 통계 출력
        total, active = get_statistics()
        
        print("\n" + "=" * 70)
        print("✅ 동기화 완료!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
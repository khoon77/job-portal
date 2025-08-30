"""
최종 통합 버전 - 20개 게시글 가져와서 Firebase 저장
"""
import sys
import io
import firebase_admin
from firebase_admin import credentials, firestore
from naraiteo_api import NaraiteoAPI
from datetime import datetime
import time

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Firebase 초기화
if not firebase_admin._apps:
    cred = credentials.Certificate("job-portal-c9d7f-firebase-adminsdk-fbsvc-b0f6caa11d.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def sync_20_jobs():
    """20개 게시글 가져와서 상세정보까지 모두 저장"""
    print("=" * 70)
    print("🔄 나라일터 20개 게시글 완전 동기화")
    print("=" * 70)
    
    api = NaraiteoAPI()
    jobs_ref = db.collection('jobs')
    
    # 1. 기본 20개 게시글 가져오기
    print("\n1️⃣ 기본 게시글 목록 가져오기...")
    jobs = api.get_job_list(page_no=1, num_of_rows=20)
    print(f"✅ {len(jobs)}개 게시글 수집")
    
    # 2. 각 게시글에 상세정보 추가
    print("\n2️⃣ 상세 정보 수집 중...")
    complete_jobs = []
    api_calls = 1  # 목록 조회 1회
    
    for i, job in enumerate(jobs, 1):
        try:
            idx = job['idx']
            title = job['title'][:40]
            
            print(f"  [{i:2}/20] {title}...")
            
            # 상세 정보 가져오기
            detail = api.get_job_detail(idx)
            api_calls += 1
            
            if detail:
                # 상세 정보로 업데이트 (지역 정보 포함)
                job.update(detail)
            
            # 파일 정보 가져오기
            files = api.get_job_files(idx)
            api_calls += 1
            job['files'] = files
            
            # 채용직급 정보 가져오기 (원본 그대로)
            position = api.get_job_position(idx)
            api_calls += 1
            if position and position.get('full_grade'):
                job['grade'] = position['full_grade']  # "간호서기 4명" 형태로 원본 그대로
            
            # 완전한 데이터 추가
            complete_jobs.append(job)
            
            # API 호출 제한 고려
            time.sleep(0.5)  # 0.5초 대기
            
        except Exception as e:
            print(f"    ❌ 오류: {e}")
            complete_jobs.append(job)  # 오류시에도 기본 정보는 저장
    
    # 3. Firebase에 저장
    print(f"\n3️⃣ Firebase 저장 중...")
    saved_count = 0
    
    for job in complete_jobs:
        try:
            doc_id = job['idx']
            
            # 저장할 데이터 준비
            job_data = {
                **job,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'last_updated': datetime.now().isoformat()
            }
            
            # 저장 (덮어쓰기)
            jobs_ref.document(doc_id).set(job_data)
            saved_count += 1
            
        except Exception as e:
            print(f"  ❌ 저장 실패 [{job.get('idx')}]: {e}")
    
    print(f"\n" + "=" * 70)
    print(f"✅ 동기화 완료:")
    print(f"   - 수집된 게시글: {len(complete_jobs)}개")
    print(f"   - Firebase 저장: {saved_count}개")
    print(f"   - 총 API 호출: {api_calls}회")
    print(f"   - 웹페이지 확인: http://localhost:8080")
    print("=" * 70)
    
    return saved_count

def verify_web_data():
    """웹페이지용 데이터 확인"""
    print("\n🌐 웹페이지 데이터 확인")
    print("-" * 50)
    
    jobs_ref = db.collection('jobs')
    docs = jobs_ref.order_by('reg_date', direction=firestore.Query.DESCENDING).limit(20).get()
    
    print(f"Firebase에서 조회된 문서: {len(docs)}개")
    
    for i, doc in enumerate(docs[:5], 1):  # 처음 5개만 표시
        data = doc.to_dict()
        title = data.get('title', 'N/A')[:45]
        contents_len = len(data.get('contents', ''))
        files_count = len(data.get('files', []))
        
        print(f"{i:2}. [{doc.id}] {title}...")
        print(f"    상세: {contents_len}자 | 파일: {files_count}개")
    
    if len(docs) > 5:
        print(f"    ... 외 {len(docs)-5}개 더")

if __name__ == "__main__":
    # 1. 20개 게시글 완전 동기화
    saved = sync_20_jobs()
    
    # 2. 웹페이지용 데이터 확인
    if saved > 0:
        verify_web_data()
    
    print(f"\n🚀 브라우저에서 http://localhost:8080 접속해서 확인하세요!")
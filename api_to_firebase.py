# api_to_firebase.py
"""
나라일터 API → Firebase 저장 → UI 연동
- 최소 5개 게시글만 수집
- 완전한 데이터 (기본 + 상세 + 파일) 수집
- Firebase 안전 저장
"""

from naraiteo_api import NaraiteoAPI
from firebase_optimized import OptimizedFirebaseService
import json

def collect_and_store_jobs():
    """API 수집 → Firebase 저장"""
    
    print("[시작] 나라일터 API -> Firebase 데이터 수집 시작")
    print("[계획] 수집 계획: 5개 게시글 (기본정보 + 상세내용 + 첨부파일)")
    
    # API 및 Firebase 초기화
    api = NaraiteoAPI()
    firebase_service = OptimizedFirebaseService()
    
    if not firebase_service.db:
        print("❌ Firebase 연결 실패")
        return
    
    # 1단계: 기본 목록 5개 수집
    print("\n1️⃣ 기본 목록 수집 중...")
    basic_jobs = api.get_job_list(num_of_rows=5)
    
    if not basic_jobs:
        print("❌ API에서 데이터를 가져올 수 없습니다")
        return
    
    print(f"✅ {len(basic_jobs)}개 기본 정보 수집 완료")
    
    # 2단계: 각 게시글의 상세정보 + 파일정보 수집
    print("\n2️⃣ 상세정보 및 첨부파일 수집 중...")
    complete_jobs = []
    
    for i, job in enumerate(basic_jobs, 1):
        job_idx = job['idx']
        print(f"   [{i}/5] {job_idx} 처리 중...")
        
        try:
            # 상세정보 가져오기
            detail = api.get_job_detail(job_idx)
            if detail and detail.get('contents'):
                job['contents'] = detail['contents']
            
            # 첨부파일 가져오기
            files = api.get_job_files(job_idx)
            job['files'] = files
            
            complete_jobs.append(job)
            print(f"   ✅ {job_idx} 완료 (파일: {len(files)}개)")
            
        except Exception as e:
            print(f"   ⚠️ {job_idx} 부분 실패: {e}")
            # 기본정보라도 저장
            job['contents'] = job.get('contents', '상세 정보를 가져올 수 없습니다.')
            job['files'] = []
            complete_jobs.append(job)
    
    print(f"\n✅ 총 {len(complete_jobs)}개 완전한 데이터 준비 완료")
    
    # 3단계: Firebase에 저장
    print("\n3️⃣ Firebase에 안전 저장 중...")
    success = firebase_service.save_jobs_batch(complete_jobs)
    
    if success:
        print("✅ Firebase 저장 완료!")
    else:
        print("❌ Firebase 저장 실패")
        return
    
    # 4단계: 저장된 데이터 검증
    print("\n4️⃣ 저장 데이터 검증 중...")
    stored_jobs = firebase_service.get_jobs_minimal(limit=5)
    
    print(f"✅ Firebase에서 {len(stored_jobs)}개 데이터 확인")
    
    # 5단계: 로컬 JSON 파일로도 백업
    print("\n5️⃣ 로컬 백업 생성 중...")
    with open('collected_jobs_backup.json', 'w', encoding='utf-8') as f:
        json.dump(complete_jobs, f, ensure_ascii=False, indent=2, default=str)
    
    print("✅ 로컬 백업 완료: collected_jobs_backup.json")
    
    # 결과 요약
    print(f"\n🎯 수집 결과 요약:")
    for job in complete_jobs:
        print(f"   📋 {job['title'][:50]}...")
        print(f"       기관: {job['dept_name']}")
        print(f"       파일: {len(job.get('files', []))}개")
        print(f"       내용: {len(job.get('contents', ''))}자")
        print()
    
    return complete_jobs

def main():
    """메인 실행 함수"""
    try:
        jobs = collect_and_store_jobs()
        if jobs:
            print("🎉 모든 작업 완료!")
            print("📱 이제 웹 UI에서 데이터를 확인할 수 있습니다.")
        else:
            print("💥 작업 실패!")
            
    except Exception as e:
        print(f"❌ 전체 작업 실패: {e}")

if __name__ == "__main__":
    main()
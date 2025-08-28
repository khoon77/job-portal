# collect_data.py
"""
완전 안전한 데이터 수집 스크립트 (윈도우 호환)
"""

from naraiteo_api import NaraiteoAPI
from firebase_safe import SafeFirebaseService
import json

def main():
    print("[시작] 데이터 수집 시작")
    
    # 서비스 초기화
    api = NaraiteoAPI()
    firebase_service = SafeFirebaseService()
    
    if not firebase_service.db:
        print("[오류] Firebase 연결 실패")
        return
    
    try:
        # 1. API에서 5개 수집
        print("[1단계] API 데이터 수집")
        jobs = api.get_job_list(num_of_rows=5)
        
        if not jobs:
            print("[오류] API 데이터 없음")
            return
            
        print(f"[수집] {len(jobs)}개 기본 정보 수집")
        
        # 2. 상세정보 추가
        print("[2단계] 상세정보 수집")
        for i, job in enumerate(jobs):
            print(f"   처리중: {i+1}/{len(jobs)} - {job['idx']}")
            
            try:
                # 상세내용
                detail = api.get_job_detail(job['idx'])
                if detail:
                    job['contents'] = detail.get('contents', '')
                
                # 파일정보
                files = api.get_job_files(job['idx'])
                job['files'] = files
                
                print(f"   완료: {len(files)}개 파일")
                
            except Exception as e:
                print(f"   경고: {e}")
                job['contents'] = ''
                job['files'] = []
        
        # 3. Firebase 저장
        print("[3단계] Firebase 저장")
        success = firebase_service.save_jobs_batch(jobs)
        
        if success:
            print("[성공] Firebase 저장 완료")
        else:
            print("[오류] Firebase 저장 실패")
            return
        
        # 4. 로컬 백업
        print("[4단계] 로컬 백업")
        with open('jobs_backup.json', 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2, default=str)
        print("[완료] 백업 파일: jobs_backup.json")
        
        # 5. 검증
        print("[5단계] 데이터 검증")
        stored = firebase_service.get_jobs_minimal(5)
        print(f"[검증] Firebase에서 {len(stored)}개 확인")
        
        # 결과 출력
        print("\n[결과 요약]")
        for i, job in enumerate(jobs, 1):
            print(f"  {i}. {job['title']}")
            print(f"     기관: {job['dept_name']}")
            print(f"     파일: {len(job.get('files', []))}개")
        
        print("\n[완료] 모든 작업 완료!")
        print("[다음] main_with_firebase.py 실행으로 서버 시작")
        
    except Exception as e:
        print(f"[오류] 작업 실패: {e}")

if __name__ == "__main__":
    main()
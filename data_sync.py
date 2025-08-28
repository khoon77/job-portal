# data_sync.py
"""
나라일터 API 데이터를 Firebase에 동기화하는 스크립트
"""

import time
from datetime import datetime
from naraiteo_api import NaraiteoAPI
from firebase_service import FirebaseJobService


class DataSyncService:
    """데이터 동기화 서비스"""
    
    def __init__(self):
        self.api = NaraiteoAPI()
        self.firebase = FirebaseJobService()
        
    def sync_latest_jobs(self, limit: int = 20):
        """최신 채용공고 동기화"""
        print(f"\n=== 채용공고 동기화 시작 ({limit}건) ===")
        start_time = datetime.now()
        
        try:
            # 1. 나라일터 API에서 최신 데이터 조회
            print("1. 나라일터 API 데이터 수집 중...")
            jobs = self.api.get_job_list(num_of_rows=limit)
            
            if not jobs:
                print("[오류] API에서 데이터를 가져올 수 없습니다")
                return False
            
            print(f"[완료] {len(jobs)}건의 채용공고 수집 완료")
            
            # 2. Firebase에 저장
            print("2. Firebase 데이터베이스 저장 중...")
            success = self.firebase.save_jobs(jobs)
            
            if success:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                print(f"[완료] 동기화 완료 - 소요시간: {duration:.2f}초")
                
                # 3. 간단한 통계 출력
                self._print_sync_summary(jobs)
                return True
            else:
                print("[오류] Firebase 저장 실패")
                return False
                
        except Exception as e:
            print(f"[오류] 동기화 중 오류 발생: {e}")
            return False
    
    def get_sync_status(self):
        """동기화 상태 확인"""
        print("\n=== 동기화 상태 확인 ===")
        
        try:
            # Firebase에서 통계 조회
            stats = self.firebase.get_statistics()
            
            if stats:
                print(f"전체 채용공고: {stats.get('total_jobs', 0)}건")
                print(f"등록 기관 수: {stats.get('total_departments', 0)}개")
                print(f"마지막 업데이트: {stats.get('last_updated', 'Unknown')}")
            else:
                print("통계 정보를 가져올 수 없습니다")
                
            # 최신 5건 공고 제목 출력
            recent_jobs = self.firebase.get_jobs(limit=5)
            if recent_jobs:
                print(f"\n최신 채용공고 {len(recent_jobs)}건:")
                for i, job in enumerate(recent_jobs, 1):
                    title = job.get('title', '')[:50]
                    dept = job.get('dept_name', '')
                    print(f"  {i}. {title}... ({dept})")
            
        except Exception as e:
            print(f"[오류] 상태 확인 중 오류: {e}")
    
    def _print_sync_summary(self, jobs):
        """동기화 요약 출력"""
        if not jobs:
            return
            
        print(f"\n동기화 요약:")
        print(f"  • 수집 공고 수: {len(jobs)}건")
        
        # 기관별 통계
        dept_count = {}
        for job in jobs:
            dept = job.get('dept_name', '미확인')
            dept_count[dept] = dept_count.get(dept, 0) + 1
        
        print(f"  • 참여 기관 수: {len(dept_count)}개")
        
        # 상위 3개 기관
        top_depts = sorted(dept_count.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_depts:
            print(f"  • 상위 기관:")
            for dept, count in top_depts:
                print(f"    - {dept}: {count}건")


def main():
    """메인 실행 함수"""
    print("나라일터 채용공고 데이터 동기화 서비스")
    print("=" * 50)
    
    sync_service = DataSyncService()
    
    # 현재 상태 확인
    sync_service.get_sync_status()
    
    # 사용자 선택
    print(f"\n실행할 작업을 선택하세요:")
    print("1. 최신 채용공고 20건 동기화")
    print("2. 최신 채용공고 50건 동기화") 
    print("3. 현재 상태만 확인")
    print("0. 종료")
    
    try:
        choice = input("\n선택 (0-3): ").strip()
        
        if choice == "1":
            sync_service.sync_latest_jobs(limit=20)
        elif choice == "2":
            sync_service.sync_latest_jobs(limit=50)
        elif choice == "3":
            print("현재 상태는 위에 표시되었습니다.")
        elif choice == "0":
            print("동기화 서비스를 종료합니다.")
        else:
            print("잘못된 선택입니다.")
            
    except KeyboardInterrupt:
        print("\n\n사용자가 중단하였습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
    
    print("\n프로그램을 종료합니다.")


if __name__ == "__main__":
    main()
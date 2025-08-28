# job_manager.py
"""
채용공고 관리 모듈
- 30일 이상 지난 게시글 삭제 (단, 마감일이 지나지 않은 경우 유지)
- 데이터베이스 정리 및 최적화
"""

from datetime import datetime, timedelta
from typing import List, Dict
import json
from firebase_service import FirebaseJobService
from naraiteo_api import NaraiteoAPI


class JobManager:
    """채용공고 데이터 관리 클래스"""
    
    def __init__(self):
        self.firebase = FirebaseJobService()
        self.api = NaraiteoAPI()
    
    def parse_date(self, date_string: str) -> datetime:
        """YYYYMMDD 형식을 datetime 객체로 변환"""
        if not date_string or len(date_string) != 8:
            return None
        
        try:
            year = int(date_string[:4])
            month = int(date_string[4:6])
            day = int(date_string[6:8])
            return datetime(year, month, day)
        except (ValueError, TypeError):
            return None
    
    def is_job_expired(self, job: Dict) -> bool:
        """게시글이 만료되었는지 확인"""
        today = datetime.now()
        cutoff_date = today - timedelta(days=30)  # 30일 전
        
        # 등록일 확인
        reg_date = self.parse_date(job.get('reg_date'))
        if not reg_date:
            return False  # 날짜가 없으면 삭제하지 않음
        
        # 마감일 확인
        end_date = self.parse_date(job.get('end_date'))
        
        # 조건:
        # 1. 등록일이 30일 이전이고
        # 2. 마감일이 오늘보다 이전이면 삭제
        if reg_date < cutoff_date:
            if not end_date:
                return True  # 마감일이 없으면 삭제
            elif end_date < today:
                return True  # 마감일이 지났으면 삭제
        
        return False  # 유지
    
    def cleanup_expired_jobs(self) -> Dict:
        """만료된 게시글 정리"""
        print("\n=== 만료된 채용공고 정리 시작 ===")
        
        if not self.firebase.db:
            print("[오류] Firebase 연결이 필요합니다")
            return {"success": False, "message": "Firebase 연결 실패"}
        
        try:
            # 모든 게시글 조회
            all_jobs = self.firebase.get_jobs(limit=1000)  # 충분히 큰 수로 모든 게시글 가져오기
            
            if not all_jobs:
                print("[정보] 정리할 게시글이 없습니다")
                return {"success": True, "message": "정리할 게시글 없음", "deleted": 0}
            
            print(f"[정보] 총 {len(all_jobs)}건의 게시글 검사 중...")
            
            # 만료된 게시글 찾기
            expired_jobs = []
            active_jobs = []
            
            for job in all_jobs:
                if self.is_job_expired(job):
                    expired_jobs.append(job)
                else:
                    active_jobs.append(job)
            
            print(f"[정보] 만료된 게시글: {len(expired_jobs)}건")
            print(f"[정보] 유지할 게시글: {len(active_jobs)}건")
            
            # 만료된 게시글 삭제
            deleted_count = 0
            if expired_jobs:
                batch = self.firebase.db.batch()
                
                for job in expired_jobs:
                    job_id = job.get('id') or job.get('idx')
                    if job_id:
                        doc_ref = self.firebase.db.collection(self.firebase.collection_name).document(str(job_id))
                        batch.delete(doc_ref)
                        deleted_count += 1
                        
                        # 삭제될 게시글 로그
                        title = job.get('title', '')[:50]
                        reg_date = job.get('reg_date', '')
                        print(f"  [삭제] {title}... (등록일: {reg_date})")
                
                # 배치 실행
                batch.commit()
                print(f"[완료] {deleted_count}건의 만료된 게시글 삭제 완료")
            
            # 통계 업데이트
            self.firebase._update_statistics(len(active_jobs))
            
            return {
                "success": True,
                "message": "만료된 게시글 정리 완료",
                "total_checked": len(all_jobs),
                "deleted": deleted_count,
                "active": len(active_jobs)
            }
            
        except Exception as e:
            print(f"[오류] 게시글 정리 실패: {e}")
            return {"success": False, "message": f"정리 실패: {str(e)}"}
    
    def sync_and_cleanup(self, limit: int = 50) -> Dict:
        """새 게시글 동기화 + 만료 게시글 정리"""
        print("\n=== 채용공고 동기화 및 정리 ===")
        
        results = {
            "sync": {"success": False, "count": 0},
            "cleanup": {"success": False, "deleted": 0}
        }
        
        try:
            # 1. 새 게시글 동기화
            print("1. 새 채용공고 동기화...")
            new_jobs = self.api.get_job_list(num_of_rows=limit)
            
            if new_jobs:
                success = self.firebase.save_jobs(new_jobs)
                results["sync"] = {
                    "success": success,
                    "count": len(new_jobs) if success else 0
                }
                print(f"[동기화] {len(new_jobs)}건 처리 완료")
            
            # 2. 만료 게시글 정리
            print("2. 만료된 게시글 정리...")
            cleanup_result = self.cleanup_expired_jobs()
            results["cleanup"] = {
                "success": cleanup_result["success"],
                "deleted": cleanup_result.get("deleted", 0)
            }
            
            # 3. 최종 통계
            final_stats = self.firebase.get_statistics()
            results["final_stats"] = final_stats
            
            print(f"\n[최종 결과]")
            print(f"  동기화: {results['sync']['count']}건")
            print(f"  삭제: {results['cleanup']['deleted']}건")
            print(f"  최종 게시글 수: {final_stats.get('total_jobs', 0)}건")
            
            return results
            
        except Exception as e:
            print(f"[오류] 동기화 및 정리 실패: {e}")
            return results
    
    def get_job_status_report(self) -> Dict:
        """게시글 상태 리포트"""
        print("\n=== 채용공고 상태 리포트 ===")
        
        try:
            all_jobs = self.firebase.get_jobs(limit=1000)
            
            if not all_jobs:
                return {"message": "게시글이 없습니다"}
            
            today = datetime.now()
            cutoff_date = today - timedelta(days=30)
            
            # 분류
            active_jobs = []        # 활성 게시글
            expiring_soon = []      # 곧 만료될 게시글 (5일 내)
            old_but_active = []     # 오래되었지만 마감일이 남은 게시글
            expired_jobs = []       # 만료된 게시글
            
            for job in all_jobs:
                reg_date = self.parse_date(job.get('reg_date'))
                end_date = self.parse_date(job.get('end_date'))
                
                if self.is_job_expired(job):
                    expired_jobs.append(job)
                elif reg_date and reg_date < cutoff_date:
                    # 30일 지났지만 마감일이 남음
                    old_but_active.append(job)
                elif end_date and (end_date - today).days <= 5:
                    # 5일 내 마감
                    expiring_soon.append(job)
                else:
                    active_jobs.append(job)
            
            report = {
                "total_jobs": len(all_jobs),
                "active_jobs": len(active_jobs),
                "expiring_soon": len(expiring_soon),
                "old_but_active": len(old_but_active),
                "expired_jobs": len(expired_jobs),
                "departments": len(set(job.get('dept_name') for job in all_jobs if job.get('dept_name'))),
                "generated_at": datetime.now().isoformat()
            }
            
            print(f"전체 게시글: {report['total_jobs']}건")
            print(f"활성 게시글: {report['active_jobs']}건")
            print(f"곧 마감: {report['expiring_soon']}건")
            print(f"오래되었지만 활성: {report['old_but_active']}건")
            print(f"만료됨: {report['expired_jobs']}건")
            print(f"참여 기관: {report['departments']}개")
            
            return report
            
        except Exception as e:
            print(f"[오류] 리포트 생성 실패: {e}")
            return {"error": str(e)}


def main():
    """테스트 및 수동 실행"""
    print("채용공고 관리 도구")
    print("=" * 40)
    
    manager = JobManager()
    
    print("\n실행할 작업을 선택하세요:")
    print("1. 상태 리포트 보기")
    print("2. 만료된 게시글 정리")
    print("3. 동기화 + 정리 (권장)")
    print("0. 종료")
    
    try:
        choice = input("\n선택 (0-3): ").strip()
        
        if choice == "1":
            manager.get_job_status_report()
        elif choice == "2":
            manager.cleanup_expired_jobs()
        elif choice == "3":
            manager.sync_and_cleanup()
        elif choice == "0":
            print("프로그램을 종료합니다.")
        else:
            print("잘못된 선택입니다.")
            
    except KeyboardInterrupt:
        print("\n\n사용자가 중단했습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")


if __name__ == "__main__":
    main()
# firebase_optimized.py
"""
한도 초과 방지를 위한 최적화된 Firebase 서비스
- 최소한의 읽기/쓰기 연산
- 효율적인 쿼리 사용
- 배치 처리 활용
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import os

class OptimizedFirebaseService:
    """최적화된 Firebase 서비스 클래스"""
    
    def __init__(self, credentials_path: str = None):
        """Firebase 초기화 (한도 초과 방지)"""
        self.db = None
        self.collection_name = "job_postings"
        
        try:
            # 중복 초기화 방지
            if not firebase_admin._apps:
                if credentials_path:
                    cred = credentials.Certificate(credentials_path)
                else:
                    # 가장 최신 파일 자동 선택
                    cred_files = [
                        "job-portal-c9d7f-firebase-adminsdk-fbsvc-b0f6caa11d.json",
                        "job-portal-scraper-15d21-firebase-adminsdk-fbsvc-27e4aa03cc.json"
                    ]
                    for file in cred_files:
                        if os.path.exists(file):
                            cred = credentials.Certificate(file)
                            print(f"[Firebase] 사용 중인 credentials: {file}")
                            break
                    else:
                        raise FileNotFoundError("Firebase credentials 파일을 찾을 수 없습니다")
                
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print("[Firebase] 연결 성공 (최적화 모드)")
            
        except Exception as e:
            print(f"[Firebase] ❌ 초기화 실패: {e}")
    
    def save_jobs_batch(self, jobs: List[Dict], max_batch_size: int = 10) -> bool:
        """배치로 공고 저장 (읽기 연산 최소화)"""
        if not self.db:
            print("[Firebase] 데이터베이스 연결이 필요합니다")
            return False
        
        try:
            total_jobs = len(jobs)
            saved_count = 0
            
            # 배치 단위로 처리
            for i in range(0, total_jobs, max_batch_size):
                batch = self.db.batch()
                batch_jobs = jobs[i:i + max_batch_size]
                
                for job in batch_jobs:
                    doc_id = str(job.get("idx"))
                    if not doc_id:
                        continue
                    
                    # 문서 참조 생성
                    doc_ref = self.db.collection(self.collection_name).document(doc_id)
                    
                    # 저장용 데이터 정리
                    job_data = self._prepare_job_data(job)
                    batch.set(doc_ref, job_data)
                    saved_count += 1
                
                # 배치 실행
                batch.commit()
                print(f"[Firebase] 배치 {i//max_batch_size + 1} 완료: {len(batch_jobs)}개")
            
            print(f"[Firebase] ✅ 총 {saved_count}개 공고 저장 완료")
            return True
            
        except Exception as e:
            print(f"[Firebase] ❌ 배치 저장 실패: {e}")
            return False
    
    def get_jobs_minimal(self, limit: int = 20) -> List[Dict]:
        """최소한의 읽기로 공고 목록 조회"""
        if not self.db:
            return []
        
        try:
            # 단일 쿼리로 필요한 만큼만 조회
            query = (self.db.collection(self.collection_name)
                    .order_by("created_at", direction=firestore.Query.DESCENDING)
                    .limit(limit))
            
            docs = query.stream()
            jobs = []
            
            for doc in docs:
                job_data = doc.to_dict()
                job_data["id"] = doc.id
                jobs.append(job_data)
            
            print(f"[Firebase] ✅ {len(jobs)}개 공고 조회 (읽기: {len(jobs)}회)")
            return jobs
            
        except Exception as e:
            print(f"[Firebase] ❌ 조회 실패: {e}")
            return []
    
    def get_job_by_id(self, job_id: str) -> Optional[Dict]:
        """단일 공고 조회 (1회 읽기만)"""
        if not self.db:
            return None
        
        try:
            doc_ref = self.db.collection(self.collection_name).document(job_id)
            doc = doc_ref.get()
            
            if doc.exists:
                job_data = doc.to_dict()
                job_data["id"] = doc.id
                print(f"[Firebase] ✅ 공고 {job_id} 조회 (읽기: 1회)")
                return job_data
            else:
                print(f"[Firebase] ⚠️ 공고 {job_id} 없음")
                return None
                
        except Exception as e:
            print(f"[Firebase] ❌ 단일 조회 실패: {e}")
            return None
    
    def get_stats_optimized(self) -> Dict:
        """최적화된 통계 조회 (집계 쿼리 사용)"""
        if not self.db:
            return {}
        
        try:
            # count() 집계 쿼리 사용 (1회 읽기만)
            collection_ref = self.db.collection(self.collection_name)
            
            # 전체 공고 수 (집계 쿼리)
            total_count = collection_ref.count().get()[0][0].value
            
            # 간단한 통계 반환 (추가 읽기 최소화)
            stats = {
                "total_jobs": total_count,
                "urgent_jobs": 0,  # 실제 구현 시 별도 필드로 관리
                "new_jobs": 0,     # 실제 구현 시 별도 필드로 관리
                "total_departments": 0,  # 실제 구현 시 별도 필드로 관리
                "last_updated": datetime.now().isoformat()
            }
            
            print(f"[Firebase] ✅ 통계 조회 (읽기: 1회)")
            return stats
            
        except Exception as e:
            print(f"[Firebase] ❌ 통계 조회 실패: {e}")
            return {}
    
    def delete_old_jobs(self, cutoff_days: int = 30) -> int:
        """오래된 공고 삭제 (배치 처리)"""
        if not self.db:
            return 0
        
        try:
            # 삭제 대상 조회 (최소한의 읽기)
            cutoff_date = datetime.now().timestamp() - (cutoff_days * 24 * 60 * 60)
            query = (self.db.collection(self.collection_name)
                    .where("created_at", "<", datetime.fromtimestamp(cutoff_date))
                    .limit(50))  # 한번에 최대 50개만
            
            docs = query.stream()
            
            # 배치 삭제
            batch = self.db.batch()
            delete_count = 0
            
            for doc in docs:
                batch.delete(doc.reference)
                delete_count += 1
            
            if delete_count > 0:
                batch.commit()
                print(f"[Firebase] ✅ {delete_count}개 오래된 공고 삭제")
            
            return delete_count
            
        except Exception as e:
            print(f"[Firebase] ❌ 삭제 실패: {e}")
            return 0
    
    def _prepare_job_data(self, job: Dict) -> Dict:
        """저장용 데이터 정리"""
        return {
            "idx": job.get("idx", ""),
            "title": job.get("title", ""),
            "dept_name": job.get("dept_name", ""),
            "reg_date": job.get("reg_date", ""),
            "end_date": job.get("end_date", ""),
            "read_count": job.get("read_count", 0),
            "grade": job.get("grade", ""),
            "work_region": job.get("work_region", ""),
            "etc_info": job.get("etc_info", ""),
            "contents": job.get("contents", ""),
            "files": job.get("files", []),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    
    def get_read_count(self) -> int:
        """현재 세션의 읽기 횟수 (디버깅용)"""
        # 실제로는 Firebase에서 직접 제공하지 않음
        # 개발 중 수동 추적 필요
        return getattr(self, '_read_count', 0)


def main():
    """안전한 테스트 스크립트"""
    print("🔥 Firebase 최적화 연결 테스트")
    
    # Firebase 서비스 초기화
    firebase_service = OptimizedFirebaseService()
    
    if firebase_service.db:
        print("✅ Firebase 연결 성공!")
        
        # 안전한 테스트 (최소한의 읽기)
        print("\n📊 통계 조회 테스트 (읽기: 1회)")
        stats = firebase_service.get_stats_optimized()
        print(f"현재 통계: {stats}")
        
        print("\n📋 공고 목록 테스트 (읽기: 최대 5회)")
        jobs = firebase_service.get_jobs_minimal(limit=5)
        print(f"조회된 공고: {len(jobs)}개")
        
        print("\n🎯 총 예상 읽기 횟수: 6회 (안전)")
    else:
        print("❌ Firebase 연결 실패")


if __name__ == "__main__":
    main()
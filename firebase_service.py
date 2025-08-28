# firebase_service.py
"""
Firebase Firestore 데이터베이스 서비스
- 채용공고 데이터 저장/조회/업데이트
- 컬렉션 관리
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from firebase_admin import credentials, firestore, initialize_app
import firebase_admin
from config import FIREBASE_CREDENTIALS_PATH, FIREBASE_PROJECT_ID


class FirebaseJobService:
    """Firebase를 이용한 채용공고 데이터 관리 서비스"""
    
    def __init__(self, credentials_path: str = FIREBASE_CREDENTIALS_PATH):
        """Firebase 초기화"""
        self.db = None
        self.collection_name = "job_postings"
        self.stats_collection = "statistics"
        
        try:
            # Firebase Admin SDK 초기화 (중복 초기화 방지)
            if not firebase_admin._apps:
                cred = credentials.Certificate(credentials_path)
                initialize_app(cred, {
                    'projectId': FIREBASE_PROJECT_ID,
                })
            
            self.db = firestore.client()
            print(f"[Firebase] 성공적으로 연결됨 - 프로젝트: {FIREBASE_PROJECT_ID}")
            
        except Exception as e:
            print(f"[Firebase] 초기화 실패: {e}")
            print(f"[Firebase] credentials 파일 경로를 확인하세요: {credentials_path}")
    
    def save_jobs(self, jobs: List[Dict]) -> bool:
        """채용공고 목록을 Firestore에 저장"""
        if not self.db:
            print("[Firebase] 데이터베이스 연결이 필요합니다")
            return False
        
        try:
            batch = self.db.batch()
            saved_count = 0
            
            for job in jobs:
                doc_id = job.get("idx")
                if not doc_id:
                    continue
                
                # 문서 참조 생성
                doc_ref = self.db.collection(self.collection_name).document(doc_id)
                
                # 저장할 데이터 정리
                job_data = self._prepare_job_data(job)
                batch.set(doc_ref, job_data, merge=True)
                saved_count += 1
            
            # 배치 커밋
            batch.commit()
            
            # 통계 업데이트
            self._update_statistics(len(jobs))
            
            print(f"[Firebase] {saved_count}건의 채용공고 저장 완료")
            return True
            
        except Exception as e:
            print(f"[Firebase] 저장 실패: {e}")
            return False
    
    def get_jobs(self, limit: int = 20, offset: int = 0) -> List[Dict]:
        """저장된 채용공고 목록 조회"""
        if not self.db:
            return []
        
        try:
            # 등록일 기준 내림차순 정렬
            query = (self.db.collection(self.collection_name)
                    .order_by("reg_date", direction=firestore.Query.DESCENDING)
                    .offset(offset)
                    .limit(limit))
            
            docs = query.stream()
            jobs = []
            
            for doc in docs:
                job_data = doc.to_dict()
                job_data["id"] = doc.id
                jobs.append(job_data)
            
            print(f"[Firebase] {len(jobs)}건의 채용공고 조회 완료")
            return jobs
            
        except Exception as e:
            print(f"[Firebase] 조회 실패: {e}")
            return []
    
    def get_job_by_id(self, job_id: str) -> Optional[Dict]:
        """특정 채용공고 상세 조회"""
        if not self.db:
            return None
        
        try:
            doc_ref = self.db.collection(self.collection_name).document(job_id)
            doc = doc_ref.get()
            
            if doc.exists:
                job_data = doc.to_dict()
                job_data["id"] = doc.id
                return job_data
            else:
                print(f"[Firebase] 문서 {job_id}를 찾을 수 없습니다")
                return None
                
        except Exception as e:
            print(f"[Firebase] 상세 조회 실패: {e}")
            return None
    
    def search_jobs(self, keyword: str = "", dept_name: str = "") -> List[Dict]:
        """채용공고 검색"""
        if not self.db:
            return []
        
        try:
            collection_ref = self.db.collection(self.collection_name)
            
            # 부서명으로 필터링
            if dept_name:
                query = collection_ref.where("dept_name", "==", dept_name)
            else:
                query = collection_ref
            
            docs = query.limit(50).stream()
            jobs = []
            
            for doc in docs:
                job_data = doc.to_dict()
                
                # 키워드가 있으면 제목에서 검색
                if keyword and keyword.lower() not in job_data.get("title", "").lower():
                    continue
                
                job_data["id"] = doc.id
                jobs.append(job_data)
            
            print(f"[Firebase] 검색 결과: {len(jobs)}건")
            return jobs
            
        except Exception as e:
            print(f"[Firebase] 검색 실패: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """채용공고 통계 조회"""
        if not self.db:
            return {}
        
        try:
            # 전체 공고 수
            total_jobs = len(list(self.db.collection(self.collection_name).stream()))
            
            # 마감 임박 공고 (예시 - 실제로는 날짜 계산 필요)
            urgent_jobs = 0  # TODO: 날짜 계산 로직 추가
            
            # 신규 공고 (7일 내)
            new_jobs = 0  # TODO: 날짜 계산 로직 추가
            
            # 기관 수
            docs = self.db.collection(self.collection_name).stream()
            departments = set()
            for doc in docs:
                dept = doc.to_dict().get("dept_name")
                if dept:
                    departments.add(dept)
            
            stats = {
                "total_jobs": total_jobs,
                "urgent_jobs": urgent_jobs,
                "new_jobs": new_jobs,
                "total_departments": len(departments),
                "last_updated": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            print(f"[Firebase] 통계 조회 실패: {e}")
            return {}
    
    def _prepare_job_data(self, job: Dict) -> Dict:
        """저장용 데이터 정리"""
        return {
            "idx": job.get("idx", ""),
            "title": job.get("title", ""),
            "dept_name": job.get("dept_name", ""),
            "reg_date": job.get("reg_date", ""),
            "end_date": job.get("end_date", ""),
            "start_date": job.get("start_date", ""),
            "read_count": job.get("read_count", 0),
            "grade": job.get("grade", ""),
            "work_region": job.get("work_region", ""),
            "etc_info": job.get("etc_info", ""),
            "file_url": job.get("file_url", ""),
            "contents": job.get("contents", ""),
            "files": job.get("files", []),
            "created_at": job.get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat()
        }
    
    def _update_statistics(self, job_count: int):
        """통계 정보 업데이트"""
        try:
            stats_ref = self.db.collection(self.stats_collection).document("general")
            stats_ref.set({
                "last_job_count": job_count,
                "last_updated": datetime.now().isoformat()
            }, merge=True)
        except Exception as e:
            print(f"[Firebase] 통계 업데이트 실패: {e}")


def main():
    """Firebase 서비스 테스트"""
    print("=== Firebase 서비스 테스트 ===")
    
    # 참고: 실제 Firebase credentials 파일이 필요합니다
    print("Firebase credentials 파일 설정이 필요합니다.")
    print("1. Firebase 콘솔에서 서비스 계정 키 생성")
    print("2. firebase-service-account.json으로 저장")
    print("3. config.py에서 프로젝트 ID 설정")
    
    # 테스트 데이터 (실제로는 naraiteo_api.py에서 가져옴)
    sample_jobs = [
        {
            "idx": "test001",
            "title": "테스트 채용공고",
            "dept_name": "테스트 기관",
            "reg_date": "20250827",
            "end_date": "20250907",
            "read_count": 10
        }
    ]
    
    # Firebase 서비스 테스트 (credentials 파일이 있을 때만 실행됨)
    try:
        firebase_service = FirebaseJobService()
        if firebase_service.db:
            # 테스트 데이터 저장
            firebase_service.save_jobs(sample_jobs)
            
            # 데이터 조회
            jobs = firebase_service.get_jobs(limit=5)
            print(f"조회된 공고 수: {len(jobs)}")
            
            # 통계 조회
            stats = firebase_service.get_statistics()
            print(f"통계: {stats}")
            
    except Exception as e:
        print(f"Firebase 테스트 실패: {e}")


if __name__ == "__main__":
    main()
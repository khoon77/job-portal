# firebase_safe.py
"""
완전 안전한 Firebase 서비스 (윈도우 호환)
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import os

class SafeFirebaseService:
    def __init__(self, credentials_path: str = None):
        self.db = None
        self.collection_name = "job_postings"
        
        try:
            if not firebase_admin._apps:
                if credentials_path:
                    cred = credentials.Certificate(credentials_path)
                else:
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
            print("[Firebase] 연결 성공")
            
        except Exception as e:
            print(f"[Firebase] 초기화 실패: {e}")
    
    def save_jobs_batch(self, jobs: List[Dict], max_batch_size: int = 10) -> bool:
        if not self.db:
            print("[Firebase] 데이터베이스 연결이 필요합니다")
            return False
        
        try:
            total_jobs = len(jobs)
            saved_count = 0
            
            for i in range(0, total_jobs, max_batch_size):
                batch = self.db.batch()
                batch_jobs = jobs[i:i + max_batch_size]
                
                for job in batch_jobs:
                    doc_id = str(job.get("idx"))
                    if not doc_id:
                        continue
                    
                    doc_ref = self.db.collection(self.collection_name).document(doc_id)
                    job_data = self._prepare_job_data(job)
                    batch.set(doc_ref, job_data)
                    saved_count += 1
                
                batch.commit()
                print(f"[Firebase] 배치 {i//max_batch_size + 1} 완료: {len(batch_jobs)}개")
            
            print(f"[Firebase] {saved_count}건의 채용공고 저장 완료")
            return True
            
        except Exception as e:
            print(f"[Firebase] 저장 실패: {e}")
            return False
    
    def get_jobs_minimal(self, limit: int = 20) -> List[Dict]:
        if not self.db:
            return []
        
        try:
            query = (self.db.collection(self.collection_name)
                    .order_by("created_at", direction=firestore.Query.DESCENDING)
                    .limit(limit))
            
            docs = query.stream()
            jobs = []
            
            for doc in docs:
                job_data = doc.to_dict()
                job_data["id"] = doc.id
                jobs.append(job_data)
            
            print(f"[Firebase] {len(jobs)}개 공고 조회")
            return jobs
            
        except Exception as e:
            print(f"[Firebase] 조회 실패: {e}")
            return []
    
    def get_job_by_id(self, job_id: str) -> Optional[Dict]:
        if not self.db:
            return None
        
        try:
            doc_ref = self.db.collection(self.collection_name).document(job_id)
            doc = doc_ref.get()
            
            if doc.exists:
                job_data = doc.to_dict()
                job_data["id"] = doc.id
                print(f"[Firebase] 공고 {job_id} 조회 성공")
                return job_data
            else:
                print(f"[Firebase] 공고 {job_id} 없음")
                return None
                
        except Exception as e:
            print(f"[Firebase] 단일 조회 실패: {e}")
            return None
    
    def get_stats_optimized(self) -> Dict:
        if not self.db:
            return {}
        
        try:
            collection_ref = self.db.collection(self.collection_name)
            total_count = collection_ref.count().get()[0][0].value
            
            stats = {
                "total_jobs": total_count,
                "urgent_jobs": 0,
                "new_jobs": 0,
                "total_departments": 0,
                "last_updated": datetime.now().isoformat()
            }
            
            print("[Firebase] 통계 조회 완료")
            return stats
            
        except Exception as e:
            print(f"[Firebase] 통계 조회 실패: {e}")
            return {}
    
    def _prepare_job_data(self, job: Dict) -> Dict:
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
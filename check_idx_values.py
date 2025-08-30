#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firebase에 저장된 job idx 고유값들 확인
"""
import sys
import io
import firebase_admin
from firebase_admin import credentials, firestore

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Firebase 초기화
if not firebase_admin._apps:
    cred = credentials.Certificate("job-portal-c9d7f-firebase-adminsdk-fbsvc-b0f6caa11d.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def check_stored_idx_values():
    print("🔍 Firebase에 저장된 job idx 고유값 확인")
    print("=" * 70)
    
    # link.txt에 있던 idx 값들
    target_idx_values = ["264910", "264927", "264926", "264917"]
    
    jobs_ref = db.collection('jobs')
    docs = jobs_ref.get()
    
    print(f"📊 총 저장된 job 문서: {len(docs)}개")
    print()
    
    stored_idx_values = []
    
    for doc in docs:
        data = doc.to_dict()
        idx = data.get('idx', '')
        title = data.get('title', 'N/A')
        
        if idx:
            stored_idx_values.append(idx)
        
        # 타겟 idx나 중요한 것들만 출력
        if idx in target_idx_values or '마산' in title or '임실' in title:
            print(f"📋 [{idx}] {title[:50]}{'...' if len(title) > 50 else ''}")
    
    print(f"\n🎯 link.txt에서 찾은 타겟 idx 값들: {target_idx_values}")
    print(f"📦 Firebase에 저장된 idx 값들 (총 {len(stored_idx_values)}개):")
    
    # idx 값들을 정렬해서 보여주기
    stored_idx_values.sort()
    for i, idx in enumerate(stored_idx_values):
        if i % 5 == 0:  # 5개씩 줄바꿈
            print()
        print(f"{idx}", end="  ")
    
    print(f"\n\n✅ 타겟 idx 중 저장된 것들:")
    for target in target_idx_values:
        if target in stored_idx_values:
            print(f"  ✓ {target} - 저장됨")
        else:
            print(f"  ✗ {target} - 누락")
    
    print(f"\n🔍 나라일터 API에서 idx를 제대로 가져오는지 확인:")
    print("  - naraiteo_api.py:279에서 idx = self._text(item, \"idx\") 로 가져옴")
    print("  - get_job_detail, get_job_files, get_job_position에서 idx 파라미터 사용")
    print("  - Firebase 저장 시 idx 필드로 저장")

if __name__ == "__main__":
    check_stored_idx_values()
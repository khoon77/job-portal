#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
업데이트된 Firebase 데이터에서 grade와 work_region 정보 확인
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

def check_grade_and_region_data():
    print("🔍 업데이트된 Firebase 데이터의 grade/work_region 정보 확인")
    print("=" * 70)
    
    jobs_ref = db.collection('jobs')
    docs = jobs_ref.order_by('reg_date', direction=firestore.Query.DESCENDING).limit(10).get()
    
    for i, doc in enumerate(docs, 1):
        data = doc.to_dict()
        title = data.get('title', 'N/A')[:50]
        grade = data.get('grade', '')
        work_region = data.get('work_region', '')
        
        print(f"{i:2}. [{doc.id}] {title}...")
        print(f"    📍 근무지역: '{work_region}' | 🏷️ 채용직급: '{grade}'")
        print()

if __name__ == "__main__":
    check_grade_and_region_data()
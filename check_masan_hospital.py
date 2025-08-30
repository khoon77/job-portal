#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
국립마산병원 데이터 확인
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

def check_masan_hospital_data():
    print("🏥 국립마산병원 데이터 확인")
    print("=" * 70)
    
    jobs_ref = db.collection('jobs')
    docs = jobs_ref.where('dept_name', '>=', '질병관리청').where('dept_name', '<=', '질병관리청\uf8ff').get()
    
    print(f"질병관리청 관련 문서: {len(docs)}개")
    
    for doc in docs:
        data = doc.to_dict()
        title = data.get('title', 'N/A')
        grade = data.get('grade', '')
        work_region = data.get('work_region', '')
        position_cnt = data.get('position_cnt', '')
        
        if '마산' in title or '간호' in title:
            print(f"\n📋 [{doc.id}] {title}")
            print(f"    📍 근무지역: '{work_region}'")
            print(f"    🏷️ 채용직급: '{grade}'")
            print(f"    👥 채용인원: '{position_cnt}'")
            
            # 모든 필드 확인
            print("    📊 전체 데이터:")
            for key, value in data.items():
                if key in ['grade', 'work_region', 'position_cnt', 'area_name', 'dept_name']:
                    print(f"        {key}: '{value}'")

if __name__ == "__main__":
    check_masan_hospital_data()
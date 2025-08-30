#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 응답 데이터 디버깅 - 실제 채용직급과 근무지역 정보 위치 확인
"""
import sys
import io
import requests
import xml.etree.ElementTree as ET
import json

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVICE_KEY = "1bmDITdGFoaDTSrbT6Uyz8bFdlIL3nydHgRu0xQtXO8SiHlCrOJKv+JNSythF12BiijhVB3qE96/4Jxr70zUNg=="
BASE_URL = "http://openapi.mpm.go.kr/openapi/service/RetrievePblinsttEmpmnInfoService"

def debug_api_response():
    print("🔍 API 응답 데이터 상세 분석")
    print("=" * 70)
    
    # 1. 먼저 목록에서 해당 공고 찾기
    print("\n1️⃣ 목록 조회 중...")
    url = f"{BASE_URL}/getList"
    params = {
        "ServiceKey": SERVICE_KEY,
        "pageNo": 1,
        "numOfRows": 20,
        "Instt_se": "g01",
        "Pblanc_ty": "e01"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        root = ET.fromstring(response.content)
        items = root.findall(".//item")
        
        target_job = None
        for item in items:
            title = item.findtext("title", "")
            if "국립마산병원" in title:
                target_job = item
                break
        
        if not target_job:
            print("❌ 국립마산병원 관련 공고를 찾을 수 없습니다.")
            return
            
        idx = target_job.findtext("idx")
        title = target_job.findtext("title")
        print(f"✅ 찾은 공고: [{idx}] {title}")
        
        # 목록에서의 모든 필드 확인
        print(f"\n📋 목록 응답의 모든 필드:")
        for child in target_job:
            value = child.text or ""
            print(f"   {child.tag}: '{value}'")
        
        # 2. 상세 정보 조회
        print(f"\n2️⃣ 상세 정보 조회 (idx: {idx})...")
        detail_url = f"{BASE_URL}/getItem"
        detail_params = {
            "ServiceKey": SERVICE_KEY,
            "idx": idx
        }
        
        detail_response = requests.get(detail_url, params=detail_params, timeout=10)
        detail_root = ET.fromstring(detail_response.content)
        detail_item = detail_root.find(".//item")
        
        if detail_item:
            print(f"📋 상세 응답의 모든 필드:")
            for child in detail_item:
                value = child.text or ""
                print(f"   {child.tag}: '{value}'")
        else:
            print("❌ 상세 정보를 가져올 수 없습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    debug_api_response()
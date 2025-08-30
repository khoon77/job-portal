#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
국립마산병원 채용직급 API 응답 상세 분석
"""
import sys
import io
import requests
import xml.etree.ElementTree as ET

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVICE_KEY = "1bmDITdGFoaDTSrbT6Uyz8bFdlIL3nydHgRu0xQtXO8SiHlCrOJKv+JNSythF12BiijhVB3qE96/4Jxr70zUNg=="
BASE_URL = "http://openapi.mpm.go.kr/openapi/service/RetrievePblinsttEmpmnInfoService"

def debug_masan_position():
    print("🏥 국립마산병원 채용직급 API 응답 상세 분석")
    print("=" * 70)
    
    # 국립마산병원 idx = 264837
    idx = "264837"
    
    print(f"\n📋 getItemPosition API 호출 (idx: {idx})")
    url = f"{BASE_URL}/getItemPosition"
    params = {
        "ServiceKey": SERVICE_KEY,
        "idx": idx
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        root = ET.fromstring(response.content)
        
        print(f"✅ API 응답 성공")
        print(f"📄 전체 XML 응답:")
        print(ET.tostring(root, encoding='unicode'))
        
        item = root.find(".//item")
        if item:
            print(f"\n📊 추출된 필드들:")
            for child in item:
                value = child.text or ""
                print(f"   {child.tag}: '{value}'")
                
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    debug_masan_position()
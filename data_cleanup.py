"""
Firebase 데이터 정리 스크립트
- 매일 대한민국 서울시각 기준 0시에 실행
- 등록일 기준 30일 지난 게시글 자동 삭제
- 30일이 안 지난 게시글들은 현행유지
"""
import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import pytz
import time
import re

def initialize_firebase():
    """Firebase 초기화"""
    if not firebase_admin._apps:
        # GitHub Actions와 로컬 모두 JSON 파일 사용
        cred = credentials.Certificate("job-portal-c9d7f-firebase-adminsdk-fbsvc-b0f6caa11d.json")
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

def parse_date_string(date_str):
    """날짜 문자열을 datetime 객체로 변환"""
    if not date_str:
        return None
    
    try:
        # YYYY-MM-DD 형식
        if len(date_str) == 10 and '-' in date_str:
            return datetime.strptime(date_str, '%Y-%m-%d')
        
        # YYYY.MM.DD 형식
        elif len(date_str) == 10 and '.' in date_str:
            return datetime.strptime(date_str, '%Y.%m.%d')
        
        # YYYYMMDD 형식
        elif len(date_str) == 8 and date_str.isdigit():
            return datetime.strptime(date_str, '%Y%m%d')
        
        return None
    except:
        return None

def clean_control_characters(text):
    """제어 문자 제거 및 텍스트 정리"""
    if not text:
        return text

    # 문자열로 변환
    text = str(text)

    # 탭과 줄바꿈은 공백으로 변환
    text = text.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')

    # 나머지 제어 문자 제거 (ASCII 0-31, 127)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

    # 연속된 공백을 하나로
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def get_seoul_time():
    """대한민국 서울 시각 기준 현재 날짜 반환"""
    seoul_tz = pytz.timezone('Asia/Seoul')
    return datetime.now(seoul_tz).replace(tzinfo=None)

def cleanup_old_jobs():
    """30일 지난 게시글 정리 (서울시각 기준)"""
    print("=" * 70)
    print("🧹 Firebase 데이터 정리 시작 (서울시각 기준)")
    
    # 서울 시각으로 현재 시간 계산
    seoul_now = get_seoul_time()
    print(f"⏰ 서울 시각: {seoul_now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        # Firebase 초기화
        db = initialize_firebase()
        
        # 현재 날짜 (서울 시각 기준)
        today = seoul_now.date()
        cutoff_date = today - timedelta(days=30)  # 30일 전
        
        print(f"📅 기준일 (서울시각): {today.strftime('%Y-%m-%d')}")
        print(f"📅 삭제 대상: {cutoff_date.strftime('%Y-%m-%d')} 이전 등록 게시글")
        
        # 모든 게시글 조회
        print("📋 모든 게시글 조회 중...")
        docs = db.collection('jobs').stream()
        
        total_count = 0
        candidates_for_deletion = []
        preserved_count = 0
        
        for doc in docs:
            try:
                total_count += 1
                data = doc.to_dict()
                doc_id = doc.id

                # 제어 문자 제거
                if 'title' in data:
                    data['title'] = clean_control_characters(data['title'])
                if 'company' in data:
                    data['company'] = clean_control_characters(data['company'])

                # 등록일 확인
                reg_date = parse_date_string(data.get('reg_date'))

                # 등록일이 30일 이상 지났는지 확인
                if reg_date and reg_date.date() <= cutoff_date:
                    # 삭제 대상
                    candidates_for_deletion.append({
                        'id': doc_id,
                        'title': data.get('title', '')[:50],
                        'reg_date': reg_date.strftime('%Y-%m-%d') if reg_date else 'N/A',
                        'company': data.get('company', '')[:30]
                    })
                else:
                    # 30일이 안 지난 게시글은 현행유지
                    preserved_count += 1

            except Exception as e:
                print(f"⚠️ 문서 처리 오류 (ID: {doc.id}): {e}")
                continue
        
        print(f"📊 전체 게시글: {total_count}개")
        print(f"📊 삭제 대상 (30일 초과): {len(candidates_for_deletion)}개")
        print(f"📊 현행유지 (30일 이내): {preserved_count}개")
        
        # 삭제 실행
        deleted_count = 0
        if candidates_for_deletion:
            print("\n🗑️ 30일 지난 게시글 삭제 실행 중...")
            
            for job in candidates_for_deletion:
                try:
                    db.collection('jobs').document(job['id']).delete()
                    deleted_count += 1
                    print(f"   ✅ 삭제: {job['title']} | {job['company']} | 등록일: {job['reg_date']}")
                    
                    # 삭제 간격 (Rate Limiting)
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"   ❌ 삭제 실패 {job['id']}: {e}")
                    continue
        else:
            print("\n💡 30일 지난 게시글이 없습니다. 모든 게시글이 현행유지됩니다.")
        
        print(f"\n✅ 정리 완료: {deleted_count}개 삭제됨, {preserved_count}개 현행유지")
        
    except Exception as e:
        print(f"❌ 데이터 정리 오류: {e}")
        sys.exit(1)

def main():
    """메인 함수"""
    try:
        # 이모지 출력 문제 해결을 위한 인코딩 설정
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

        cleanup_old_jobs()
        print("🎉 데이터 정리 작업 완료 (서울시각 기준)")

    except Exception as e:
        print(f"💥 치명적 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

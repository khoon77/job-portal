"""
Firebase 데이터 정리 스크립트
- 등록일 기준 30일 지난 게시글 삭제
- 단, 마감일이 안 지난 게시글은 유지
"""
import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import time

def initialize_firebase():
    """Firebase 초기화"""
    if not firebase_admin._apps:
        # GitHub Actions에서는 환경변수로 인증키 전달
        if os.getenv('GITHUB_ACTIONS'):
            # GitHub Secrets에서 Firebase 인증 정보 가져오기
            firebase_config = {
                "type": "service_account",
                "project_id": os.getenv('FIREBASE_PROJECT_ID'),
                "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
                "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
                "client_id": os.getenv('FIREBASE_CLIENT_ID'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL')
            }
            
            cred = credentials.Certificate(firebase_config)
        else:
            # 로컬 실행시에는 파일 사용
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

def cleanup_old_jobs():
    """오래된 게시글 정리"""
    print("=" * 70)
    print("🧹 Firebase 데이터 정리 시작")
    print(f"⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        # Firebase 초기화
        db = initialize_firebase()
        
        # 현재 날짜
        today = datetime.now()
        cutoff_date = today - timedelta(days=30)  # 30일 전
        
        print(f"📅 기준일: {today.strftime('%Y-%m-%d')}")
        print(f"📅 삭제 기준: {cutoff_date.strftime('%Y-%m-%d')} 이전 등록")
        
        # 모든 게시글 조회
        print("📋 모든 게시글 조회 중...")
        docs = db.collection('jobs').stream()
        
        total_count = 0
        candidates_for_deletion = []
        preserved_count = 0
        
        for doc in docs:
            total_count += 1
            data = doc.to_dict()
            doc_id = doc.id
            
            # 등록일 확인
            reg_start_date = parse_date_string(data.get('reg_start_date'))
            reg_end_date = parse_date_string(data.get('reg_end_date'))  # 마감일
            
            # 등록일이 30일 이상 지났는지 확인
            if reg_start_date and reg_start_date < cutoff_date:
                # 마감일이 아직 안 지났으면 보존
                if reg_end_date and reg_end_date >= today:
                    preserved_count += 1
                    print(f"   💾 보존: {data.get('title', '')[:50]} (마감일: {reg_end_date.strftime('%Y-%m-%d')})")
                else:
                    # 삭제 대상
                    candidates_for_deletion.append({
                        'id': doc_id,
                        'title': data.get('title', '')[:50],
                        'reg_start_date': reg_start_date.strftime('%Y-%m-%d') if reg_start_date else 'N/A',
                        'reg_end_date': reg_end_date.strftime('%Y-%m-%d') if reg_end_date else 'N/A'
                    })
        
        print(f"📊 전체 게시글: {total_count}개")
        print(f"📊 삭제 대상: {len(candidates_for_deletion)}개")
        print(f"📊 마감일로 보존: {preserved_count}개")
        
        # 삭제 실행
        deleted_count = 0
        if candidates_for_deletion:
            print("\n🗑️ 삭제 실행 중...")
            
            for job in candidates_for_deletion:
                try:
                    db.collection('jobs').document(job['id']).delete()
                    deleted_count += 1
                    print(f"   ✅ 삭제: {job['title']} (등록: {job['reg_start_date']}, 마감: {job['reg_end_date']})")
                    
                    # 삭제 간격 (Rate Limiting)
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"   ❌ 삭제 실패 {job['id']}: {e}")
                    continue
        
        print(f"\n✅ 정리 완료: {deleted_count}개 삭제됨")
        
    except Exception as e:
        print(f"❌ 데이터 정리 오류: {e}")
        sys.exit(1)

def main():
    """메인 함수"""
    try:
        cleanup_old_jobs()
        print("🎉 데이터 정리 완료")
        
    except Exception as e:
        print(f"💥 치명적 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
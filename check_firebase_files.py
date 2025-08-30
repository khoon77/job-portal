"""Firebase에 저장된 파일 정보 확인"""
import firebase_admin
from firebase_admin import credentials, firestore
import sys
import io

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Firebase 초기화
if not firebase_admin._apps:
    cred = credentials.Certificate("job-portal-c9d7f-firebase-adminsdk-fbsvc-b0f6caa11d.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

print("=" * 70)
print("Firebase 파일 정보 저장 상태 확인")
print("=" * 70)

# jobs 컬렉션에서 5개 문서 가져오기
docs = db.collection('jobs').limit(5).get()

for i, doc in enumerate(docs, 1):
    data = doc.to_dict()
    idx = doc.id
    title = data.get('title', 'N/A')[:40]
    files = data.get('files', [])
    
    print(f"\n{i}. 문서 ID: {idx}")
    print(f"   제목: {title}...")
    print(f"   파일 개수: {len(files)}개")
    
    if files:
        for j, file_info in enumerate(files[:2], 1):  # 처음 2개만 표시
            filename = file_info.get('filename', 'N/A')
            filepath = file_info.get('filepath', 'N/A')
            download_url = file_info.get('download_url', 'N/A')
            filesize = file_info.get('filesize', 'N/A')
            
            print(f"   파일 {j}:")
            print(f"     - 파일명: {filename}")
            print(f"     - 기존경로: {filepath[:50]}..." if len(str(filepath)) > 50 else f"     - 기존경로: {filepath}")
            print(f"     - 다운로드URL: {download_url[:60]}..." if len(str(download_url)) > 60 else f"     - 다운로드URL: {download_url}")
            print(f"     - 크기: {filesize}")
        
        if len(files) > 2:
            print(f"   ... 외 {len(files) - 2}개 파일 더")
    else:
        print("   ⚠️ 파일 정보 없음")

print("\n" + "=" * 70)
print("확인 완료")
print("=" * 70)
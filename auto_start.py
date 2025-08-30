"""
자동 작업 환경 복구 스크립트
클로드 재시작 시 이전 작업 상태를 자동으로 복구합니다.
"""
import os
import json
import subprocess
import webbrowser
import time
import sys
import io

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def auto_start():
    try:
        # 프로젝트 경로로 이동
        project_path = r'C:\Users\hoon7\PycharmProjects\NewJobPortal'
        os.chdir(project_path)
        print(f"✅ 프로젝트 디렉토리 이동: {project_path}")
        
        # 세션 정보 읽기
        session_file = 'CLAUDE_SESSION.json'
        if os.path.exists(session_file):
            with open(session_file, 'r', encoding='utf-8') as f:
                session = json.load(f)
            print(f"📋 세션 정보 로드 완료")
        else:
            print("⚠️ 세션 파일이 없습니다. 기본값으로 시작합니다.")
            session = {
                "last_working_file": "index_v1-1.html",
                "server_port": 8080
            }
        
        # 1. 서버 시작
        port = session.get('server_port', 8080)
        print(f"🚀 로컬 서버 시작 (포트: {port})...")
        
        # 백그라운드로 서버 실행
        server_process = subprocess.Popen(
            [sys.executable, '-m', 'http.server', str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # 서버 시작 대기
        time.sleep(3)
        
        # 2. 브라우저 열기
        file_name = session.get('last_working_file', 'index_v1-1.html')
        url = f'http://localhost:{port}/{file_name}'
        print(f"🌐 브라우저 열기: {url}")
        webbrowser.open(url)
        
        # 3. 작업 상태 표시
        print("\n" + "="*60)
        print("✅ 작업 환경 복구 완료!")
        print("="*60)
        print(f"📂 작업 파일: {file_name}")
        print(f"🌐 서버 포트: {port}")
        print(f"📝 버전: {session.get('current_version', 'v1-1')}")
        print(f"📅 마지막 업데이트: {session.get('last_update', 'N/A')}")
        
        if 'issues_resolved' in session:
            print("\n✅ 해결된 문제들:")
            for issue in session['issues_resolved']:
                print(f"  - {issue}")
        
        print("\n💡 서버 종료: Ctrl+C")
        print("="*60)
        
        # 서버 프로세스 유지
        try:
            server_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 서버 종료됨")
            server_process.terminate()
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("\n수동으로 시작하려면:")
        print("1. cd C:\\Users\\hoon7\\PycharmProjects\\NewJobPortal")
        print("2. python -m http.server 8080")
        print("3. 브라우저에서 http://localhost:8080/index_v1-1.html 열기")

if __name__ == "__main__":
    auto_start()
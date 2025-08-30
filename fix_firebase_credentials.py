#!/usr/bin/env python3
"""
GitHub Actions용 Firebase 인증 파일 정리 스크립트
제어 문자 제거 및 JSON 유효성 검증
"""
import sys
import json
import os

def main():
    try:
        # 환경변수에서 Firebase 인증 정보 가져오기
        credentials = os.environ.get('FIREBASE_CREDENTIALS', '')
        if not credentials:
            print('FIREBASE_CREDENTIALS environment variable not found')
            sys.exit(1)
        
        print(f'Credentials length: {len(credentials)} characters')
        
        # 제어 문자 제거
        cleaned = ''.join(char for char in credentials if ord(char) >= 32 or char in '\n\r\t')
        cleaned = cleaned.strip()
        
        print(f'Cleaned credentials length: {len(cleaned)} characters')
        
        # JSON 파싱 테스트
        data = json.loads(cleaned)
        print('JSON parsing successful')
        
        # 올바른 형식으로 파일 생성
        output_file = 'job-portal-c9d7f-firebase-adminsdk-fbsvc-b0f6caa11d.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f'Firebase credentials file created: {output_file}')
        print(f'File contains keys: {list(data.keys())[:5]}')
        
    except json.JSONDecodeError as e:
        print(f'JSON parsing error: {e}')
        print(f'Error at line {e.lineno}, column {e.colno}')
        sys.exit(1)
    except Exception as e:
        print(f'Error processing credentials: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
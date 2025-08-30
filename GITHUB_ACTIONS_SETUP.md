# GitHub Actions 자동화 설정 가이드

## 🎯 구현된 자동화 기능

### 1. 신규 게시글 자동 동기화
- **주기**: 5분마다 실행
- **기능**: 나라일터에서 신규 게시글만 수집하여 Firebase에 저장
- **파일**: `auto_sync_scheduler.py`

### 2. 오래된 데이터 자동 정리
- **주기**: 매일 오전 2시 (UTC)
- **기능**: 30일 지난 게시글 삭제 (단, 마감일 안 지난 것은 유지)
- **파일**: `data_cleanup.py`

## 🔑 GitHub Secrets 설정 필수

GitHub 리포지토리의 Settings > Secrets and variables > Actions에서 다음 Secrets를 추가해야 합니다:

### Firebase 인증 정보
```
FIREBASE_PROJECT_ID: job-portal-c9d7f
FIREBASE_PRIVATE_KEY_ID: [Firebase 인증키 파일의 private_key_id]
FIREBASE_PRIVATE_KEY: [Firebase 인증키 파일의 private_key - 줄바꿈 포함]
FIREBASE_CLIENT_EMAIL: firebase-adminsdk-fbsvc@job-portal-c9d7f.iam.gserviceaccount.com
FIREBASE_CLIENT_ID: [Firebase 인증키 파일의 client_id]
FIREBASE_CLIENT_CERT_URL: [Firebase 인증키 파일의 client_x509_cert_url]
```

## 📋 설정 단계별 가이드

### 1단계: Firebase 인증키 정보 복사
현재 프로젝트의 `job-portal-c9d7f-firebase-adminsdk-fbsvc-b0f6caa11d.json` 파일에서 각 값들을 복사합니다.

### 2단계: GitHub Secrets 추가
1. https://github.com/khoon77/job-portal/settings/secrets/actions 접속
2. "New repository secret" 클릭
3. 위의 6개 Secret을 각각 추가

### 3단계: 워크플로우 활성화
- 파일을 GitHub에 push하면 자동으로 활성화됩니다
- Actions 탭에서 실행 상태 확인 가능

## ⚠️ 중요 고려사항

### GitHub Actions 무료 제한
- **월 2,000분 제한**: 5분마다 실행 시 월 8,640분 사용 (무료 한도 초과)
- **주의**: 무료 계정에서는 한도 초과 시 과금될 수 있음
- **대안**: 필요시 10분 또는 15분 주기로 조정 가능

### Firebase 사용량
- **읽기/쓰기 횟수 증가**: 5분마다 API 호출로 사용량 증가
- **예상 비용**: 무료 할당량 내에서 사용 가능하지만 모니터링 필요

### 실행 시간대
- **UTC 기준**: 한국시간 +9시간 차이
- **데이터 정리**: UTC 2시 = 한국시간 오전 11시

## 🚀 수동 실행 방법

### GitHub Actions에서 수동 실행
1. GitHub 리포지토리 > Actions 탭
2. 원하는 워크플로우 선택
3. "Run workflow" 버튼 클릭

### 로컬에서 테스트
```bash
# 신규 게시글 동기화
python auto_sync_scheduler.py

# 데이터 정리
python data_cleanup.py
```

## 📊 모니터링

### Actions 탭에서 확인 가능한 정보
- ✅ 성공/실패 상태
- ⏱️ 실행 시간
- 📋 로그 및 오류 메시지
- 📈 실행 히스토리

### 로그 메시지 예시
```
🔄 신규 게시글 자동 동기화 시작
📋 기존 게시글: 20개
🆕 신규 게시글: 3개
✅ 신규 게시글 3개 저장 완료
🎉 자동 동기화 완료
```

## 🔧 워크플로우 수정 방법

### 실행 주기 변경
```yaml
# .github/workflows/auto-sync.yml
schedule:
  - cron: '*/15 * * * *'  # 15분마다
  - cron: '0 */1 * * *'   # 1시간마다
```

### 데이터 보존 기간 변경
```python
# data_cleanup.py
cutoff_date = today - timedelta(days=45)  # 45일로 변경
```

## 🚨 문제 해결

### 자주 발생하는 문제
1. **Firebase 인증 오류**: Secrets 설정 확인
2. **API 호출 제한**: 요청 간격 조정 필요
3. **실행 시간 초과**: 처리량 제한 필요

### 긴급 중지 방법
1. GitHub Actions 탭에서 워크플로우 비활성화
2. 또는 `.github/workflows/` 파일들 삭제

---

**설정 완료 후 자동으로 나라일터 최신 게시글이 실시간으로 업데이트됩니다!** 🎉
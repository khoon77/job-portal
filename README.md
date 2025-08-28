# 🏛️ 나라일터 채용정보 포털

공공기관 채용공고를 한눈에 볼 수 있는 현대적인 웹 애플리케이션

## 🌟 주요 기능

- 📊 **실시간 통계**: 전체/임박/최근 채용공고 수, 등록기관 수
- 🔍 **스마트 검색**: 기관명이나 제목으로 빠른 검색
- 📋 **카드형 리스트**: D-Day 표시, 기관별 색상 구분  
- 📄 **상세보기 모달**: 채용 내용, 첨부파일, 관련 링크
- ⭐ **북마크 기능**: 관심 채용공고 저장
- 📱 **반응형 디자인**: 모바일/태블릿 최적화
- 🎨 **현대적 UI**: 그라데이션, 애니메이션 효과

## 🛠️ 기술 스택

### Backend
- **FastAPI**: 고성능 Python 웹 프레임워크
- **Firebase Firestore**: NoSQL 데이터베이스
- **나라일터 API**: 공공데이터 연동

### Frontend
- **Vanilla JavaScript**: 가볍고 빠른 클라이언트
- **Modern CSS**: 그라데이션, 애니메이션, 반응형
- **PWA Ready**: 오프라인 지원 준비

### DevOps
- **GitHub Actions**: CI/CD 파이프라인
- **Vercel**: 자동 배포 및 호스팅
- **pytest**: 자동화 테스트

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone <repository-url>
cd NewJobPortal
```

### 2. 가상환경 설정
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux  
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 실제 API 키와 설정 입력
```

### 5. Firebase 설정
1. Firebase Console에서 프로젝트 생성
2. 서비스 계정 키 다운로드
3. `firebase-service-account.json`으로 저장

### 6. 서버 실행
```bash
python main.py
```

http://localhost:8001 에서 애플리케이션 확인

## 📁 프로젝트 구조

```
NewJobPortal/
├── .github/workflows/     # GitHub Actions
├── tests/                 # 테스트 파일
├── main.py               # FastAPI 메인 애플리케이션
├── config.py             # 설정 파일
├── naraiteo_api.py       # 나라일터 API 클라이언트
├── firebase_service.py   # Firebase 서비스
├── index.html            # 프론트엔드
├── vercel.json           # Vercel 배포 설정
├── requirements.txt      # Python 의존성
└── README.md
```

## 🔧 API 엔드포인트

### 채용공고
- `GET /api/jobs/list` - 채용공고 목록
- `GET /api/jobs/detail/{id}` - 채용공고 상세정보
- `GET /api/jobs/content/{id}` - 채용공고 상세내용
- `GET /api/jobs/files/{id}` - 첨부파일 목록
- `GET /api/jobs/stats` - 통계 정보

### 관리
- `GET /health` - 서버 상태 확인
- `POST /api/jobs/sync` - 데이터 동기화
- `POST /api/jobs/cleanup` - 만료된 데이터 정리

## 🧪 테스트

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함
pytest --cov=. --cov-report=html

# 특정 테스트 파일
pytest tests/test_main.py -v
```

## 📝 코드 품질

```bash
# 코드 포맷팅
black .

# 임포트 정렬
isort .

# 린팅
flake8 .

# 보안 검사
safety check -r requirements.txt
bandit -r .
```

## 🚢 배포

### Vercel 자동 배포
1. GitHub에 코드 푸시
2. Vercel에서 프로젝트 연결
3. 환경 변수 설정
4. 자동 배포 완료

### 환경 변수 (Vercel)
```
NARAITEO_API_KEY=your_api_key
FIREBASE_PROJECT_ID=your_project_id  
FIREBASE_CREDENTIALS_PATH=./firebase-creds.json
```

## 📊 모니터링

- **GitHub Actions**: CI/CD 파이프라인 상태
- **Vercel Analytics**: 사이트 방문자 통계
- **Firebase Console**: 데이터베이스 사용량

## 🤝 기여하기

1. Fork 생성
2. Feature 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add AmazingFeature'`)
4. 브랜치에 Push (`git push origin feature/AmazingFeature`) 
5. Pull Request 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 지원

문제가 있으시면 [Issues](../../issues)에서 문의해주세요.

---

Made with ❤️ for Korean Public Job Portal
# minimal_test.py
"""
극도로 제한적인 Firebase 테스트
- 최대 3개 샘플 데이터만 사용
- 총 읽기 횟수: 5회 미만
- 총 쓰기 횟수: 3회 미만
- 한도 절대 초과 방지
"""

from firebase_optimized import OptimizedFirebaseService
from datetime import datetime

# 극도로 제한된 샘플 데이터 (3개만!)
MINIMAL_SAMPLE_JOBS = [
    {
        "idx": "test001",
        "title": "2025년 테스트 채용공고 1",
        "dept_name": "테스트 기관 1",
        "reg_date": "20250828",
        "end_date": "20250908",
        "read_count": 100,
        "grade": "9급",
        "work_region": "서울특별시",
        "etc_info": "일반채용",
        "contents": "테스트용 상세 내용입니다.",
        "files": [
            {
                "filename": "test1.pdf",
                "filepath": "/test/path1.pdf",
                "filesize": "1MB"
            }
        ]
    },
    {
        "idx": "test002", 
        "title": "2025년 테스트 채용공고 2",
        "dept_name": "테스트 기관 2", 
        "reg_date": "20250828",
        "end_date": "20250915",
        "read_count": 200,
        "grade": "8급",
        "work_region": "부산광역시", 
        "etc_info": "경력채용",
        "contents": "테스트용 상세 내용 2입니다.",
        "files": []
    }
]

def safe_firebase_test():
    """안전한 Firebase 테스트 (한도 초과 절대 방지)"""
    
    print("🔥 극도로 제한적인 Firebase 테스트 시작")
    print("⚠️ 예상 사용량: 읽기 5회, 쓰기 2회 (매우 안전)")
    
    # 사용자 확인
    confirm = input("\n계속 진행하시겠습니까? (y/n): ").lower()
    if confirm != 'y':
        print("테스트 취소됨")
        return
    
    # Firebase 서비스 초기화
    firebase_service = OptimizedFirebaseService()
    
    if not firebase_service.db:
        print("❌ Firebase 연결 실패")
        return
    
    # 연산 카운터
    read_count = 0
    write_count = 0
    
    try:
        print("\n1️⃣ 현재 통계 확인 (읽기: 1회)")
        stats_before = firebase_service.get_stats_optimized()
        read_count += 1
        print(f"   현재 공고 수: {stats_before.get('total_jobs', 0)}")
        
        print("\n2️⃣ 샘플 데이터 저장 (쓰기: 2회)")
        success = firebase_service.save_jobs_batch(MINIMAL_SAMPLE_JOBS, max_batch_size=5)
        write_count += 2
        
        if success:
            print("   ✅ 샘플 데이터 저장 성공")
        else:
            print("   ❌ 저장 실패")
            return
        
        print("\n3️⃣ 저장된 데이터 확인 (읽기: 2회)")
        jobs = firebase_service.get_jobs_minimal(limit=2)
        read_count += 2
        print(f"   조회된 공고: {len(jobs)}개")
        
        for job in jobs:
            print(f"   - {job.get('title', 'N/A')}")
        
        print("\n4️⃣ 특정 공고 상세 조회 (읽기: 1회)")
        if jobs:
            first_job = firebase_service.get_job_by_id(jobs[0].get('id'))
            read_count += 1
            if first_job:
                print(f"   상세 조회 성공: {first_job.get('title')}")
        
        print("\n5️⃣ 최종 통계 확인 (읽기: 1회)")
        stats_after = firebase_service.get_stats_optimized()
        read_count += 1
        print(f"   최종 공고 수: {stats_after.get('total_jobs', 0)}")
        
        print(f"\n📊 총 사용량:")
        print(f"   읽기: {read_count}회 (한도 50,000회의 {read_count/50000*100:.3f}%)")
        print(f"   쓰기: {write_count}회 (한도 20,000회의 {write_count/20000*100:.3f}%)")
        print(f"   ✅ 매우 안전한 수준!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
    
    print("\n🎯 테스트 완료!")

def connection_test_only():
    """연결 테스트만 (읽기/쓰기 없음)"""
    print("🔗 Firebase 연결 테스트만 실행")
    
    firebase_service = OptimizedFirebaseService()
    
    if firebase_service.db:
        print("✅ Firebase 연결 성공!")
        print("🔥 Firestore 클라이언트 정상 작동")
        print("📊 연산 사용량: 0회 (완전 안전)")
    else:
        print("❌ Firebase 연결 실패")

if __name__ == "__main__":
    print("Firebase 테스트 옵션:")
    print("1. 연결 테스트만 (연산 0회)")  
    print("2. 제한적 데이터 테스트 (연산 7회)")
    
    choice = input("\n선택하세요 (1 또는 2): ").strip()
    
    if choice == "1":
        connection_test_only()
    elif choice == "2":
        safe_firebase_test()
    else:
        print("잘못된 선택입니다.")
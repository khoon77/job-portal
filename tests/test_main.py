"""
메인 API 엔드포인트 테스트
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_main():
    """메인 페이지 테스트"""
    response = client.get("/")
    assert response.status_code == 200

def test_health_check():
    """헬스 체크 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

def test_jobs_list_api():
    """채용공고 목록 API 테스트"""
    response = client.get("/api/jobs/list")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data

def test_jobs_stats_api():
    """채용공고 통계 API 테스트"""
    response = client.get("/api/jobs/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data

def test_job_detail_api():
    """채용공고 상세 API 테스트"""
    response = client.get("/api/jobs/detail/test123")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data

def test_job_content_api():
    """채용공고 내용 API 테스트"""
    response = client.get("/api/jobs/content/test123")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data

def test_job_files_api():
    """채용공고 첨부파일 API 테스트"""
    response = client.get("/api/jobs/files/test123")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
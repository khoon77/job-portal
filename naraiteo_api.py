# naraiteo_api.py
"""
나라일터(공공채용정보) API 연동 모듈
- 채용공고 목록 조회
- 채용공고 상세 조회  
- 첨부파일 정보 조회
"""

import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# API 설정
SERVICE_KEY = "1bmDITdGFoaDTSrbT6Uyz8bFdlIL3nydHgRu0xQtXO8SiHlCrOJKv+JNSythF12BiijhVB3qE96/4Jxr70zUNg=="
BASE_URL = "http://openapi.mpm.go.kr/openapi/service/RetrievePblinsttEmpmnInfoService"
TIMEOUT = 3

class NaraiteoAPI:
    """나라일터 API 클래스"""
    
    def __init__(self):
        self.service_key = SERVICE_KEY
        self.base_url = BASE_URL
        
    def _text(self, element, tag: str, default: str = "") -> str:
        """XML 요소에서 텍스트 추출"""
        value = element.findtext(tag)
        return value if value is not None else default
    
    def _convert_area_code_to_name(self, area_code: str) -> str:
        """지역코드를 지역명으로 변환"""
        if not area_code:
            return ""
        
        # 상세 지역코드 맵핑 (시군구 포함)
        detailed_area_map = {
            # 전라북도
            "45000": "전라북도",
            "45130": "전라북도 군산시",
            "45140": "전라북도 익산시", 
            "45180": "전라북도 정읍시",
            "45190": "전라북도 남원시",
            "45210": "전라북도 김제시",
            "45710": "전라북도 완주군",
            "45720": "전라북도 진안군",
            "45730": "전라북도 무주군",
            "45740": "전라북도 장수군",
            "45750": "전라북도 임실군",
            "45770": "전라북도 순창군",
            "45790": "전라북도 고창군",
            "45800": "전라북도 부안군",
            
            # 경상남도  
            "48000": "경상남도",
            "48120": "경상남도 진주시",
            "48125": "경상남도 창원시",  # 마산시 포함
            "48127": "경상남도 통영시",
            "48129": "경상남도 사천시",
            "48170": "경상남도 김해시",
            "48220": "경상남도 밀양시",
            "48240": "경상남도 거제시",
            "48250": "경상남도 양산시",
            "48720": "경상남도 의령군",
            "48730": "경상남도 함안군",
            "48740": "경상남도 창녕군",
            "48820": "경상남도 고성군",
            "48840": "경상남도 남해군",
            "48850": "경상남도 하동군",
            "48860": "경상남도 산청군",
            "48870": "경상남도 함양군",
            "48880": "경상남도 거창군",
            "48890": "경상남도 합천군",
        }
        
        # 상세 코드 먼저 확인
        if area_code in detailed_area_map:
            return detailed_area_map[area_code]
        
        # 5자리 지역코드인 경우 앞 2자리만 사용
        if len(area_code) == 5:
            area_code = area_code[:2]
            
        area_map = {
            "11": "서울특별시",
            "26": "부산광역시", 
            "27": "대구광역시",
            "28": "인천광역시",
            "29": "광주광역시",
            "30": "대전광역시",
            "31": "울산광역시",
            "36": "세종특별자치시",
            "41": "경기도",
            "43": "충청북도",
            "44": "충청남도",
            "45": "전라북도",
            "46": "전라남도",
            "47": "경상북도",
            "48": "경상남도",
            "50": "제주특별자치도",
            "51": "강원도",
        }
        return area_map.get(area_code, "")
    
    def _extract_grade_from_text(self, text: str) -> str:
        """텍스트에서 채용직급 추출 (제목 또는 타입정보)"""
        if not text:
            return ""
        
        # 일반적인 공무원 직급 키워드 검색 (우선순위대로)
        grade_patterns = [
            ("9급", "9급"),
            ("8급", "8급"), 
            ("7급", "7급"),
            ("6급", "6급"),
            ("5급", "5급"),
            ("인턴", "인턴"),
            ("청년인턴", "인턴"),
            ("전문연구원", "전문연구원"),
            ("선임연구원", "선임연구원"),  
            ("책임연구원", "책임연구원"),
            ("연구원", "연구원"),
            ("공무직", "공무직"),
            ("전문임기제", "전문직"),
            ("전문직", "전문직"),
            ("기능직", "기능직"),
            ("임기제", "임기제"),
            ("무기계약직", "무기계약직"),
            ("계약직", "계약직"),
            ("경력채용", "경력직"),
            ("경력경쟁", "경력직"),
            ("운전", "운전직"),
            ("서기보", "서기보"),
            ("안전관리", "안전관리"),
            ("사무관", "사무관"),
            ("주무관", "주무관"),
            ("연구사", "연구사"),
            ("기술직", "기술직"),
            ("사회복무요원", "사회복무요원")
        ]
        
        for pattern, grade in grade_patterns:
            if pattern in text:
                return grade
        
        return ""  # 알 수 없는 경우 빈 값 반환
    
    def _extract_region_from_title(self, title: str) -> str:
        """제목에서 지역 정보 추출"""
        if not title:
            return ""
            
        # 주요 지역 키워드 검색
        regions = [
            "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
            "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
            "경기도", "강원도", "충청북도", "충청남도", "전라북도", "전라남도", 
            "경상북도", "경상남도", "제주도"
        ]
        
        for region in regions:
            if region in title:
                if region in ["경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남"]:
                    return region + "도"
                elif region in ["서울", "부산", "대구", "인천", "광주", "대전", "울산"]:
                    return region + "광역시" if region != "서울" else "서울특별시"
                else:
                    return region
        
        return ""
    
    def _extract_region_from_contents(self, contents: str) -> str:
        """게시글 내용에서 상세 지역 정보 추출"""
        if not contents:
            return ""
        
        import re
        
        # 상세 지역 정보 패턴들 (우선순위 순)
        patterns = [
            # "전라북도 임실군", "경상남도 마산시" 등 (공백 포함)
            r"([가-힣]+도)\s+([가-힣]+[시군구])",
            # "경기도 화성시", "충청남도 천안시" 등  
            r"([가-힣]+도)\s+([가-힣]+시)",
            # "서울특별시 강남구", "부산광역시 해운대구" 등
            r"([가-힣]+[특별광역]시)\s+([가-힣]+구)",
            # "임실우체국", "마산병원" 등에서 지역명 추출
            r"([가-힣]+)[우체국|병원|교도소|법원|경찰서]",
            # "임실군", "마산시" 등 단독
            r"([가-힣]+[시군구])",
            # "전라북도", "경상남도" 등
            r"([가-힣]+도)",
            # "서울특별시", "부산광역시" 등
            r"([가-힣]+[특별광역]시)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, contents)
            if matches:
                if isinstance(matches[0], tuple):
                    return " ".join(matches[0])
                else:
                    return matches[0]
        
        return ""
    
    def _make_request(self, endpoint: str, params: Dict) -> Optional[ET.Element]:
        """API 요청 공통 함수"""
        url = f"{self.base_url}/{endpoint}"
        params["ServiceKey"] = self.service_key
        
        try:
            print(f"[API 요청] {endpoint}: {params}")
            response = requests.get(url, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # 에러 응답 체크
            result_code = root.findtext(".//resultCode")
            if result_code and result_code != "00":
                result_msg = root.findtext(".//resultMsg")
                print(f"[API 에러] {result_code}: {result_msg}")
                return None
                
            return root
            
        except requests.RequestException as e:
            print(f"[네트워크 오류] {e}")
            return None
        except ET.ParseError as e:
            print(f"[XML 파싱 오류] {e}")
            return None
    
    def get_job_list(self, page_no: int = 1, num_of_rows: int = 20) -> List[Dict]:
        """채용공고 목록 조회"""
        params = {
            "pageNo": page_no,
            "numOfRows": num_of_rows,
            "Instt_se": "g01",    # 국가기관
            "Pblanc_ty": "e01"    # 공무원 채용
        }
        
        root = self._make_request("getList", params)
        if not root:
            return []
        
        jobs = []
        items = root.findall(".//item")
        
        for item in items:
            # 디버깅: 실제 데이터 값 확인
            area_code = self._text(item, "areaCode")
            type_info = self._text(item, "typeinfo02")
            
            if len(jobs) == 0:  # 첫 번째 항목만 로깅
                print(f"[디버그] areaCode: '{area_code}', typeinfo02: '{type_info}'")
                print(f"[디버그] title: '{self._text(item, 'title')}'")
            
            # 지역코드를 지역명으로 변환
            area_name = self._convert_area_code_to_name(area_code)
            
            # 제목에서 직급 추출
            title = self._text(item, "title")
            grade_info = self._extract_grade_from_text(title)
            
            # 타입 정보에서도 직급 추출 시도 (제목에서 찾지 못한 경우)
            if not grade_info:
                grade_info = self._extract_grade_from_text(type_info)
            
            # 지역 정보가 없으면 제목에서 추출 시도
            if not area_name:
                region_from_title = self._extract_region_from_title(title)
                if region_from_title:
                    area_name = region_from_title
            
            job_data = {
                "idx": self._text(item, "idx"),
                "title": title,
                "dept_name": self._text(item, "deptName"),
                "reg_date": self._text(item, "regdate"),
                "end_date": self._text(item, "enddate"),
                "start_date": "",
                "read_count": int(self._text(item, "readnum", "0")),
                "grade": grade_info or "미확인",
                "work_region": area_name or "미확인",
                "etc_info": type_info or "일반채용",
                "file_url": "",
                "contents": "",
                "area_code": area_code,
                "username": self._text(item, "username"),
                "mod_date": self._text(item, "moddate"),
                "created_at": datetime.now().isoformat()
            }
            jobs.append(job_data)
        
        print(f"[수집 완료] {len(jobs)}건의 채용공고")
        return jobs
    
    def get_job_detail(self, idx: str) -> Optional[Dict]:
        """채용공고 상세 정보 조회"""
        params = {"idx": idx}
        
        root = self._make_request("getItem", params)
        if not root:
            return None
        
        item = root.find(".//item")
        if item is None:
            return None
        
        # 상세에서 지역 정보 추출
        area_nm = self._text(item, "areaNm")
        area_code = self._text(item, "areaCode")
        work_addr = self._text(item, "workAddr")  # 상세 근무주소 추가
        contents = self._text(item, "contents")
        
        # 지역 정보 우선순위: workAddr(상세주소) > area_nm(API제공) > 지역코드변환 > 정보없음
        if work_addr:
            # 상세 근무주소가 있으면 우선 사용
            work_region = work_addr
        elif area_nm:
            # areaNm이 있으면 그대로 사용
            work_region = area_nm
        elif area_code:
            # 지역코드를 지역명으로 변환
            work_region = self._convert_area_code_to_name(area_code)
        else:
            work_region = "정보없음"
        
        detail_data = {
            "idx": idx,
            "title": self._text(item, "title"),
            "contents": contents,
            "dept_name": self._text(item, "deptName"),
            "reg_date": self._text(item, "regdate"),
            "end_date": self._text(item, "enddate"),
            "read_count": int(self._text(item, "readnum", "0")),
            "area_name": area_nm,           # 상세에서 제공되는 지역명
            "area_code": area_code,         # 상세에서 제공되는 지역코드
            "work_region": work_region,     # 가장 상세한 지역 정보 사용
            "updated_at": datetime.now().isoformat()
        }
        
        print(f"[상세 조회] 공고 ID {idx} 상세정보 획득 - 근무지역: {work_region}")
        return detail_data
    
    def get_job_files(self, idx: str) -> List[Dict]:
        """채용공고 첨부파일 목록 조회"""
        params = {
            "idx": idx,
            "pageNo": 1,
            "numOfRows": 50
        }
        
        root = self._make_request("getItemFile", params)
        if not root:
            return []
        
        files = []
        items = root.findall(".//item")
        
        for item in items:
            filename = self._text(item, "filename")
            filepath = self._text(item, "filepath")
            filesize = self._text(item, "filesize")
            
            # API 가이드에 따라 완전한 다운로드 URL 구성
            # 형식: https://www.gojobs.go.kr/downFile.do?filenm=파일명&uuid=값&saveGbn=employ
            if filepath:
                # filepath에서 uuid와 saveGbn 추출 (API 응답 형식에 따라)
                if "downFile.do" in filepath:
                    download_url = f"https://www.gojobs.go.kr/{filepath}"
                else:
                    # filepath가 부분적인 경우, 완전한 URL 구성
                    download_url = f"https://www.gojobs.go.kr/downFile.do?filenm={filename}&uuid={filepath}&saveGbn=employ"
            else:
                download_url = ""
            
            file_data = {
                "filename": filename,
                "filepath": filepath,  # 원본 filepath 보존
                "download_url": download_url,  # 완전한 다운로드 URL 추가
                "filesize": filesize,
                "job_idx": idx
            }
            files.append(file_data)
        
        print(f"[첨부파일] 공고 ID {idx}: {len(files)}개 파일")
        return files
    
    def get_job_position(self, idx: str) -> Optional[Dict]:
        """채용직급 정보 조회 - 정확한 채용직급과 인원수 정보"""
        params = {"idx": idx}
        
        root = self._make_request("getItemPosition", params)
        if not root:
            return None
        
        item = root.find(".//item")
        if item is None:
            return None
        
        name = self._text(item, "name")
        cnt = self._text(item, "cnt")
        
        # 원본 그대로 조합: "간호서기" + "4명" = "간호서기 4명"
        if cnt and cnt != "0":
            full_grade = f"{name} {cnt}명"
        else:
            full_grade = name
        
        position_data = {
            "idx": idx,
            "parentidx": self._text(item, "parentidx"),
            "code": self._text(item, "code"),
            "name": name,
            "cnt": cnt,
            "full_grade": full_grade,  # 완전한 채용직급 정보
            "updated_at": datetime.now().isoformat()
        }
        
        print(f"[채용직급] 공고 ID {idx}: {full_grade}")
        return position_data
    
    def get_enriched_jobs(self, limit: int = 10) -> List[Dict]:
        """상세정보가 보강된 채용공고 목록"""
        # 1. 기본 목록 가져오기
        jobs = self.get_job_list(num_of_rows=min(limit, 100))
        
        enriched_jobs = []
        
        for job in jobs[:limit]:
            idx = job["idx"]
            
            # 2. 상세정보 보강
            detail = self.get_job_detail(idx)
            if detail:
                # 상세정보로 기본정보 업데이트
                job.update({k: v for k, v in detail.items() if v})
            
            # 3. 첨부파일 정보 추가
            files = self.get_job_files(idx)
            job["files"] = files
            
            enriched_jobs.append(job)
        
        print(f"[보강 완료] {len(enriched_jobs)}건의 완전한 채용공고 정보")
        return enriched_jobs


def main():
    """테스트 실행"""
    api = NaraiteoAPI()
    
    print("=== 나라일터 API 테스트 ===")
    
    # 1. 기본 목록 조회 테스트
    print("\n1. 채용공고 목록 조회 (3건)")
    jobs = api.get_job_list(num_of_rows=3)
    
    for job in jobs:
        print(f"  - {job['title'][:50]}...")
        print(f"    기관: {job['dept_name']}")
        print(f"    접수기간: {job['reg_date']} ~ {job['end_date']}")
    
    if jobs:
        # 2. 상세 정보 조회 테스트
        first_job_idx = jobs[0]["idx"]
        print(f"\n2. 첫 번째 공고 상세 조회 (ID: {first_job_idx})")
        detail = api.get_job_detail(first_job_idx)
        if detail:
            print(f"  - 상세 내용: {detail['contents'][:100]}...")
        
        # 3. 첨부파일 조회 테스트
        print(f"\n3. 첫 번째 공고 첨부파일 조회")
        files = api.get_job_files(first_job_idx)
        for file in files:
            print(f"  - {file['filename']}")
    
    # 4. 통합 데이터 조회 테스트
    print(f"\n4. 보강된 채용공고 2건 조회")
    enriched = api.get_enriched_jobs(limit=2)
    
    print("\n=== 최종 데이터 샘플 ===")
    if enriched:
        sample = enriched[0]
        print(json.dumps(sample, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
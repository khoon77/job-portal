#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firestore의 채용공고를 기반으로 크롤러가 읽을 수 있는 정적 상세 페이지(jobs/{idx}/index.html)와
sitemap.xml을 생성한다. GitHub Actions에서 auto_sync_scheduler.py 실행 뒤 호출되어 결과물을 커밋한다.

jobs 컬렉션은 data_cleanup.py가 등록 30일 경과 문서를 완전히 삭제하는 방식으로 관리되므로,
컬렉션에 남아있는 문서는 전부 "현재 유효한" 공고로 취급한다(공공기관 채용정보 포털과 달리
status 필드로 active를 걸러낼 필요가 없음).
"""

import os
import json
import logging
from datetime import datetime, timedelta, timezone

from firebase_admin import firestore
import firebase_admin

from firebase_utils import load_firebase_credentials

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SITE_URL = "https://korea-jobportal.co.kr"
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
JOBS_DIR = os.path.join(REPO_ROOT, "jobs")
SITEMAP_PATH = os.path.join(REPO_ROOT, "sitemap.xml")
KST = timezone(timedelta(hours=9))

REGION_ADDRESS_FALLBACKS = {
    "서울": ("서울특별시", "서울특별시 중구 세종대로 110", "04524"),
    "부산": ("부산광역시", "부산광역시 연제구 중앙대로 1001", "47545"),
    "대구": ("대구광역시", "대구광역시 중구 공평로 88", "41911"),
    "인천": ("인천광역시", "인천광역시 남동구 정각로 29", "21554"),
    "광주": ("광주광역시", "광주광역시 서구 내방로 111", "61945"),
    "대전": ("대전광역시", "대전광역시 서구 둔산로 100", "35242"),
    "울산": ("울산광역시", "울산광역시 남구 중앙로 201", "44675"),
    "세종": ("세종특별자치시", "세종특별자치시 한누리대로 2130", "30151"),
    "경기": ("경기도", "경기도 수원시 영통구 도청로 30", "16508"),
    "강원": ("강원특별자치도", "강원특별자치도 춘천시 중앙로 1", "24266"),
    "충북": ("충청북도", "충청북도 청주시 상당구 상당로 82", "28515"),
    "충남": ("충청남도", "충청남도 홍성군 홍북읍 충남대로 21", "32255"),
    "전북": ("전북특별자치도", "전북특별자치도 전주시 완산구 효자로 225", "54968"),
    "전남": ("전라남도", "전라남도 무안군 삼향읍 오룡길 1", "58564"),
    "경북": ("경상북도", "경상북도 안동시 풍천면 도청대로 455", "36759"),
    "경남": ("경상남도", "경상남도 창원시 의창구 중앙대로 300", "51154"),
    "제주": ("제주특별자치도", "제주특별자치도 제주시 문연로 6", "63122"),
    "전국": ("대한민국", "대한민국", "00000"),
}


def structured_address(work_region):
    region_text = (work_region or "전국").strip()
    primary_region = region_text.replace("·", ",").replace("/", ",").split(",")[0].strip() or "전국"
    for key, (address_region, street_address, postal_code) in REGION_ADDRESS_FALLBACKS.items():
        if key in primary_region:
            return {
                "@type": "PostalAddress",
                "streetAddress": street_address,
                "addressLocality": primary_region,
                "addressRegion": address_region,
                "postalCode": postal_code,
                "addressCountry": "KR",
            }
    return {
        "@type": "PostalAddress",
        "streetAddress": f"{primary_region} 근무지",
        "addressLocality": primary_region,
        "addressRegion": primary_region,
        "postalCode": "00000",
        "addressCountry": "KR",
    }


STATIC_PAGES = [
    ("/", "daily", "1.0"),
    ("/about.html", "monthly", "0.8"),
    ("/contact.html", "monthly", "0.5"),
    ("/privacy.html", "yearly", "0.3"),
    ("/terms.html", "yearly", "0.3"),
]


def init_firestore():
    if firebase_admin._apps:
        return firestore.client()
    cred, source = load_firebase_credentials()
    logger.info(f"Firebase 인증 정보 로드: {source}")
    firebase_admin.initialize_app(cred)
    return firestore.client()


def esc(value):
    if value is None:
        return ''
    return (str(value)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def format_detail_content(text):
    if not text or not str(text).strip():
        return '<p>상세 내용은 첨부파일을 참고해 주세요.</p>'
    lines = [esc(line) for line in str(text).split('\n') if line.strip()]
    return ''.join(f'<p>{line}</p>' for line in lines)


def format_iso_date(raw):
    """YYYYMMDD 형식 문자열을 YYYY-MM-DD로 변환. 파싱 불가하면 None."""
    raw = (raw or '').strip()
    if len(raw) == 8 and raw.isdigit():
        try:
            return datetime.strptime(raw, '%Y%m%d').strftime('%Y-%m-%d')
        except ValueError:
            return None
    return None


def guess_employment_type(grade):
    grade = grade or ''
    if '인턴' in grade:
        return 'INTERN'
    if '무기계약' in grade:
        return 'FULL_TIME'
    if '계약' in grade:
        return 'CONTRACTOR'
    return 'OTHER'


def build_job_json_ld(job, page_url):
    data = {
        "@context": "https://schema.org/",
        "@type": "JobPosting",
        "title": job.get('title', ''),
        "description": job.get('contents') or job.get('title', ''),
        "identifier": {
            "@type": "PropertyValue",
            "name": job.get('dept_name', ''),
            "value": job.get('idx', ''),
        },
        "employmentType": guess_employment_type(job.get('grade', '')),
        "hiringOrganization": {
            "@type": "Organization",
            "name": job.get('dept_name', ''),
        },
        "jobLocation": {
            "@type": "Place",
            "address": structured_address(job.get('work_region', '')),
        },
        "directApply": False,
        "url": page_url,
    }
    date_posted = format_iso_date(job.get('reg_date'))
    if date_posted:
        data["datePosted"] = date_posted
    # end_date가 '99991231'이면 상시채용을 뜻하므로 validThrough를 생략한다.
    if job.get('end_date') != '99991231':
        valid_through = format_iso_date(job.get('end_date'))
        if valid_through:
            data["validThrough"] = f"{valid_through}T23:59:59+09:00"
    # 스크립트 태그 조기 종료 방지
    return json.dumps(data, ensure_ascii=False).replace('</', '<\\/')


def build_files_section(files):
    if not files:
        return ''
    items = []
    for f in files:
        filename = esc(f.get('filename', '첨부파일'))
        url = esc(f.get('download_url') or f.get('filepath') or '#')
        items.append(f'<li><a href="{url}" target="_blank" rel="noopener">{filename}</a></li>')
    return (
        '<h2 style="font-size:18px; margin:24px 0 10px; color:#1e293b;">첨부파일</h2>'
        f'<ul style="padding-left:20px; color:#1565c0;">{"".join(items)}</ul>'
    )


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | 대한민국 취업정보 코리아잡포털</title>
    <meta name="description" content="{description}">
    <meta name="robots" content="{robots}">
    <link rel="canonical" href="{canonical}">

    <meta property="og:title" content="{title} | 대한민국 취업정보 코리아잡포털">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{canonical}">
    <meta property="og:site_name" content="대한민국 취업정보 코리아잡포털">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@100;200;300;400;500;600;700;800;900&display=swap" rel="stylesheet">

    <script type="application/ld+json">
    {json_ld}
    </script>

    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Noto Sans KR', 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f5f6fa 0%, #e8eaf0 100%);
            color: #2c3e50;
            line-height: 1.8;
            min-height: 100vh;
        }}
        .header {{ background: #ffffff; padding: 30px 0; border-bottom: 1px solid #e0e0e0; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
        .header-content {{ max-width: 900px; margin: 0 auto; padding: 0 20px; display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ font-size: 24px; font-weight: 700; color: #1565c0; }}
        .header a {{ color: #1565c0; text-decoration: none; font-weight: 600; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 40px 20px; }}
        .job-wrapper {{ background: white; border-radius: 16px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); }}
        h1.job-title {{ font-size: 28px; font-weight: 700; color: #1a202c; margin-bottom: 20px; }}
        .job-meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; background: #f8fafc; border-radius: 12px; padding: 20px; margin-bottom: 30px; }}
        .job-meta div {{ font-size: 15px; color: #475569; }}
        .job-meta strong {{ color: #1e293b; }}
        .job-content {{ color: #334155; margin-bottom: 30px; }}
        .job-content p {{ margin-bottom: 12px; }}
        .home-link {{ display: inline-block; padding: 12px 22px; background: #eef2f7; color: #1565c0; text-decoration: none; border-radius: 8px; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1>💼 코리아잡포털</h1>
            <a href="/">← 전체 채용정보 보기</a>
        </div>
    </div>
    <div class="container">
        <div class="job-wrapper">
            {closed_banner}
            <h1 class="job-title">{title}</h1>
            <div class="job-meta">
                <div><strong>기관명</strong><br>{dept_name}</div>
                <div><strong>근무지역</strong><br>{work_region}</div>
                <div><strong>채용직급</strong><br>{grade}</div>
                <div><strong>등록일</strong><br>{reg_date}</div>
                <div><strong>마감일</strong><br>{end_date}</div>
            </div>
            <div class="job-content">
                {detail_content}
                {files_section}
            </div>
            <a class="home-link" href="/">전체 채용정보 목록</a>
        </div>
    </div>
</body>
</html>
"""

CLOSED_BANNER = (
    '<div style="background:#fef3c7; border-left:4px solid #f59e0b; padding:16px 20px; '
    'border-radius:8px; margin-bottom:24px; color:#92400e; font-weight:600;">'
    '⚠️ 마감된 채용공고입니다. 접수기간이 종료되어 더 이상 지원할 수 없습니다.</div>'
)


def display_date(raw):
    iso = format_iso_date(raw)
    if iso:
        return iso
    if raw == '99991231':
        return '상시채용'
    return raw or '-'


def render_job_page(job, closed=False):
    idx = job.get('idx', '')
    canonical = f"{SITE_URL}/jobs/{idx}/"
    title = esc(job.get('title', '제목 없음'))
    dept_name = esc(job.get('dept_name', '-'))
    description = esc(f"{job.get('dept_name', '')} - {job.get('title', '')} | {job.get('work_region', '')} 채용공고")[:150]

    return PAGE_TEMPLATE.format(
        title=title,
        description=description,
        robots="noindex, follow" if closed else "index, follow",
        canonical=canonical,
        json_ld=build_job_json_ld(job, canonical),
        closed_banner=CLOSED_BANNER if closed else "",
        dept_name=dept_name,
        work_region=esc(job.get('work_region', '-')),
        grade=esc(job.get('grade', '-')),
        reg_date=esc(display_date(job.get('reg_date'))),
        end_date=esc(display_date(job.get('end_date'))),
        detail_content=format_detail_content(None) if closed else format_detail_content(job.get('contents')),
        files_section='' if closed else build_files_section(job.get('files')),
    )


def load_jobs(db):
    """jobs 컬렉션은 30일 경과 문서가 data_cleanup.py로 완전 삭제되므로 전량이 유효 공고다.
    나라일터 API의 idx(recrutPblntSn)는 항상 숫자이므로, 숫자가 아닌 문서 ID는
    테스트/더미 데이터로 간주해 정적 페이지·sitemap에서 제외한다."""
    docs = db.collection('jobs').stream()
    jobs = []
    skipped = []
    for doc in docs:
        if not str(doc.id).isdigit():
            skipped.append(doc.id)
            continue
        data = doc.to_dict()
        data['idx'] = doc.id
        jobs.append(data)
    if skipped:
        logger.warning(f"숫자가 아닌 idx 문서 {len(skipped)}건 제외 (테스트/더미 데이터로 추정): {skipped}")
    return jobs


def write_job_pages(jobs):
    os.makedirs(JOBS_DIR, exist_ok=True)
    active_ids = set()

    for job in jobs:
        idx = job.get('idx')
        if not idx:
            continue
        active_ids.add(str(idx))
        job_dir = os.path.join(JOBS_DIR, str(idx))
        os.makedirs(job_dir, exist_ok=True)
        with open(os.path.join(job_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(render_job_page(job, closed=False))

    # Firestore에서 삭제된(30일 경과) 공고는 파일을 지우지 않고 "마감됨" 배너로 전환해
    # 이미 색인/공유된 링크가 깨지지 않도록 유지한다.
    if os.path.isdir(JOBS_DIR):
        for existing_idx in os.listdir(JOBS_DIR):
            if existing_idx in active_ids:
                continue
            job_file = os.path.join(JOBS_DIR, existing_idx, 'index.html')
            if not os.path.isfile(job_file):
                continue
            with open(job_file, 'r', encoding='utf-8') as f:
                content = f.read()
            if '마감된 채용공고입니다' in content:
                continue  # 이미 마감 처리됨
            closed_job = {'idx': existing_idx, 'title': '마감된 채용공고'}
            with open(job_file, 'w', encoding='utf-8') as f:
                f.write(render_job_page(closed_job, closed=True))
            logger.info(f"만료 처리: jobs/{existing_idx}")

    logger.info(f"채용공고 정적 페이지 {len(active_ids)}건 생성 완료")
    return active_ids


def write_sitemap(active_ids):
    now = datetime.now(KST).strftime('%Y-%m-%d')
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']

    for path, freq, priority in STATIC_PAGES:
        lines.append('  <url>')
        lines.append(f'    <loc>{SITE_URL}{path}</loc>')
        lines.append(f'    <lastmod>{now}</lastmod>')
        lines.append(f'    <changefreq>{freq}</changefreq>')
        lines.append(f'    <priority>{priority}</priority>')
        lines.append('  </url>')

    for idx in sorted(active_ids):
        lines.append('  <url>')
        lines.append(f'    <loc>{SITE_URL}/jobs/{idx}/</loc>')
        lines.append(f'    <lastmod>{now}</lastmod>')
        lines.append('    <changefreq>weekly</changefreq>')
        lines.append('    <priority>0.7</priority>')
        lines.append('  </url>')

    lines.append('</urlset>')

    with open(SITEMAP_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    logger.info(f"sitemap.xml 재생성 완료 ({len(STATIC_PAGES) + len(active_ids)}개 URL)")


def main():
    db = init_firestore()
    jobs = load_jobs(db)
    logger.info(f"채용공고 {len(jobs)}건 로드")
    active_ids = write_job_pages(jobs)
    write_sitemap(active_ids)


if __name__ == "__main__":
    main()

"""
AX 기반 공공임대주택 시설물 안전·유지관리 최적화 및 지능형 행정 자동화 솔루션
주관: (주)에이톰엔지니어링 | 참여: 세종대학교 × 한국화재보험협회(방재시험연구원)
위탁: (사)첨단기술안전점검협회(HSIA) | 자문: 한국건설기술연구원(KICT)
수요처: 서울주택도시공사(SH) × 경상북도개발공사

국토교통부 AX-SPRINT 과제 프로토타입 (2026)
실행: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, date
import random
import time
from PIL import Image, ImageDraw, ImageFont
import io

# ══════════════════════════════════════════════════════
# 전역 설정
# ══════════════════════════════════════════════════════
st.set_page_config(
    page_title="에이톰-AX | 공공주택 안전관리 플랫폼",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS
st.markdown("""
<style>
/* 전체 배경 */
.main { background: #f8fafc; }

/* KPI 카드 */
.kpi-card {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
    border-radius: 14px; padding: 18px 20px; color: white;
    margin-bottom: 10px; box-shadow: 0 4px 15px rgba(37,99,235,0.3);
}
.kpi-card .label { font-size: 12px; opacity: 0.8; font-weight: 500; letter-spacing: 0.5px; }
.kpi-card .value { font-size: 30px; font-weight: 800; margin: 4px 0; }
.kpi-card .sub   { font-size: 11px; opacity: 0.7; }

.kpi-card-green {
    background: linear-gradient(135deg, #065f46 0%, #059669 100%);
    border-radius: 14px; padding: 18px 20px; color: white;
    margin-bottom: 10px; box-shadow: 0 4px 15px rgba(5,150,105,0.3);
}
.kpi-card-green .label { font-size: 12px; opacity: 0.8; }
.kpi-card-green .value { font-size: 30px; font-weight: 800; margin: 4px 0; }
.kpi-card-green .sub   { font-size: 11px; opacity: 0.7; }

.kpi-card-red {
    background: linear-gradient(135deg, #7f1d1d 0%, #dc2626 100%);
    border-radius: 14px; padding: 18px 20px; color: white;
    margin-bottom: 10px; box-shadow: 0 4px 15px rgba(220,38,38,0.3);
}
.kpi-card-red .label { font-size: 12px; opacity: 0.8; }
.kpi-card-red .value { font-size: 30px; font-weight: 800; margin: 4px 0; }
.kpi-card-red .sub   { font-size: 11px; opacity: 0.7; }

.kpi-card-amber {
    background: linear-gradient(135deg, #78350f 0%, #d97706 100%);
    border-radius: 14px; padding: 18px 20px; color: white;
    margin-bottom: 10px; box-shadow: 0 4px 15px rgba(217,119,6,0.3);
}
.kpi-card-amber .label { font-size: 12px; opacity: 0.8; }
.kpi-card-amber .value { font-size: 30px; font-weight: 800; margin: 4px 0; }
.kpi-card-amber .sub   { font-size: 11px; opacity: 0.7; }

/* 알림 박스 */
.alert-critical { background:#fef2f2; border-left:4px solid #dc2626; padding:10px 14px; border-radius:6px; margin:5px 0; font-size:13px; }
.alert-warning  { background:#fffbeb; border-left:4px solid #d97706; padding:10px 14px; border-radius:6px; margin:5px 0; font-size:13px; }
.alert-ok       { background:#f0fdf4; border-left:4px solid #16a34a; padding:10px 14px; border-radius:6px; margin:5px 0; font-size:13px; }
.alert-info     { background:#eff6ff; border-left:4px solid #2563eb; padding:10px 14px; border-radius:6px; margin:5px 0; font-size:13px; }

/* 섹션 헤더 */
.sh { font-size:17px; font-weight:700; color:#1e3a5f; border-bottom:2px solid #2563eb; padding-bottom:5px; margin:20px 0 12px 0; }

/* RPA 자동화율 바 */
.rpa-row { display:flex; align-items:center; margin:8px 0; gap:10px; }
.rpa-label { width:180px; font-size:13px; font-weight:500; color:#374151; }
.rpa-bar-bg { flex:1; height:18px; background:#e5e7eb; border-radius:9px; overflow:hidden; }
.rpa-bar-fill { height:100%; border-radius:9px; display:flex; align-items:center; padding-left:8px; font-size:11px; color:white; font-weight:600; }
.rpa-pct { width:45px; font-size:13px; font-weight:700; color:#1e3a5f; text-align:right; }

/* 태그 */
.tag-high { background:#fef2f2; color:#dc2626; border:1px solid #fca5a5; border-radius:999px; padding:2px 10px; font-size:11px; font-weight:600; }
.tag-mid  { background:#fffbeb; color:#b45309; border:1px solid #fcd34d; border-radius:999px; padding:2px 10px; font-size:11px; font-weight:600; }
.tag-low  { background:#f0fdf4; color:#15803d; border:1px solid #86efac; border-radius:999px; padding:2px 10px; font-size:11px; font-weight:600; }

/* 단계 카드 */
.step-card { background:white; border:1px solid #e5e7eb; border-radius:10px; padding:14px; margin:6px 0; }
.step-title { font-weight:700; color:#1e3a5f; font-size:14px; }
.step-desc  { font-size:12px; color:#6b7280; margin-top:4px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# 상수 정의 (문서 기반)
# ══════════════════════════════════════════════════════
COMPLEXES_SH = [
    "SH 강남 매입임대 A (준공: 1998년, 220세대)",
    "SH 마포 영구임대 B (준공: 2001년, 480세대)",
    "SH 노원 국민임대 C (준공: 2004년, 620세대)",
    "SH 강서 행복주택 D (준공: 2018년, 310세대)",
    "SH 서초 매입임대 E (준공: 1996년, 185세대)",
]
COMPLEXES_GB = [
    "경북개발공사 구미 영구임대 A (준공: 2002년, 290세대)",
    "경북개발공사 안동 국민임대 B (준공: 2005년, 380세대)",
]
ALL_COMPLEXES = COMPLEXES_SH + COMPLEXES_GB

# 민원 유형 (문서 기반)
COMPLAINT_TYPES = {
    "누수": {"위험도": "중", "rpa자동화": 70, "색상": "#3b82f6"},
    "균열·구조손상": {"위험도": "고", "rpa자동화": 70, "색상": "#ef4444"},
    "화재·가연성외벽": {"위험도": "고", "rpa자동화": 70, "색상": "#f97316"},
    "시설노후": {"위험도": "저", "rpa자동화": 70, "색상": "#8b5cf6"},
    "관리비이의": {"위험도": "저", "rpa자동화": 100, "색상": "#06b6d4"},
    "계약관련": {"위험도": "저", "rpa자동화": 100, "색상": "#84cc16"},
    "기타": {"위험도": "저", "rpa자동화": 70, "색상": "#94a3b8"},
}

# ══════════════════════════════════════════════════════
# 샘플 데이터 생성 함수 (문서 기반 현실적 수치)
# ══════════════════════════════════════════════════════
np.random.seed(2026)
random.seed(2026)

def make_iot_data(days=30):
    """IoT 센서 시계열 데이터 (온도·습도·전력·진동·CO)"""
    now = datetime.now()
    rows = []
    for h in range(days * 24):
        ts = now - timedelta(hours=(days * 24 - h))
        rows.append({
            "ts": ts,
            "온도": 21 + 7 * np.sin(h / 24 * np.pi) + np.random.normal(0, 0.4),
            "습도": 54 + 18 * np.sin(h / 24 * np.pi + 0.8) + np.random.normal(0, 1.2),
            "전력_kWh": max(0, 2.1 + 1.5 * np.sin(h / 24 * np.pi + 0.5) + np.random.normal(0, 0.2)),
            "진동_g": abs(np.random.normal(0, 0.15)) + (0.85 if 190 < h < 210 else 0),
            "CO_ppm": max(0, 1.8 + abs(np.random.normal(0, 0.2)) + (16 if 390 < h < 402 else 0)),
        })
    return pd.DataFrame(rows)

def make_complaints(n=80):
    """민원 데이터 (RPA 자동화율 포함)"""
    types = list(COMPLAINT_TYPES.keys())
    statuses = ["접수", "AI분류완료", "담당자배정", "현장처리중", "완료", "분쟁종결"]
    status_w = [0.08, 0.12, 0.15, 0.25, 0.30, 0.10]
    rows = []
    for i in range(n):
        t = random.choice(types)
        days_ago = random.randint(0, 120)
        st_val = random.choices(statuses, weights=status_w)[0]
        done = days_ago if st_val in ("완료", "분쟁종결") else None
        rows.append({
            "민원번호": f"CM-2026-{1000+i:04d}",
            "수요처": random.choice(["SH공사", "경북개발공사"]),
            "단지": random.choice(ALL_COMPLEXES)[:18] + "..",
            "유형": t,
            "위험도": COMPLAINT_TYPES[t]["위험도"],
            "접수일": (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
            "상태": st_val,
            "처리일수": done,
            "AI분류": "자동" if random.random() < 0.85 else "수동",
            "AI신뢰도": round(random.uniform(0.72, 0.97), 2),
            "손해산정액_만원": random.randint(30, 800) if st_val in ("완료", "분쟁종결") else None,
            "담당자": random.choice(["김관리", "이점검", "박시설", "최행정"]),
        })
    return pd.DataFrame(rows)

def make_inspection():
    """점검 이력 데이터"""
    rows = []
    for cpx in ALL_COMPLEXES:
        built_year = int(cpx.split("준공: ")[1][:4])
        age = 2026 - built_year
        for m in range(12):
            month = (datetime.now() - timedelta(days=30 * m)).strftime("%Y-%m")
            base_crack = max(0, int(age / 5) + random.randint(-1, 3))
            rows.append({
                "단지": cpx[:16] + "..",
                "점검월": month,
                "경과년수": age,
                "균열건수": base_crack,
                "누수건수": random.randint(0, 4),
                "드라이비트_취약": random.randint(0, 2),
                "화재위험건수": random.randint(0, 2),
                "노후도점수": max(20, 95 - age * 1.8 + random.uniform(-5, 5)),
                "점검방법": random.choice(["드론스캔", "앱업로드", "현장점검"]),
            })
    return pd.DataFrame(rows)

def make_facilities():
    """시설물 대장 (세움터 연동 데이터)"""
    rows = []
    for cpx in ALL_COMPLEXES:
        built_year = int(cpx.split("준공: ")[1][:4])
        age = 2026 - built_year
        세대수 = int(cpx.split("세대)")[0].split(", ")[-1])
        rows.append({
            "단지": cpx[:20],
            "준공년도": built_year,
            "경과년수": age,
            "세대수": 세대수,
            "외벽재질": random.choice(["드라이비트", "타일", "노출콘크리트", "알루미늄복합판넬"]),
            "방수공법": random.choice(["우레탄", "시트", "도막"]),
            "노후도점수": round(max(20, 95 - age * 1.8 + random.uniform(-5, 5)), 1),
            "FMS연동": random.choice(["연동완료", "연동완료", "미연동"]),
            "세움터연동": random.choice(["연동완료", "진행중"]),
            "마지막드론점검": (datetime.now() - timedelta(days=random.randint(10, 90))).strftime("%Y-%m-%d"),
        })
    return pd.DataFrame(rows)

def make_damage_detections():
    """AI 손상 탐지 결과 목록 (문서 기반)"""
    items = [
        {"위치": "강남A동 외벽 3층 북측", "유형": "수직균열", "폭_mm": 0.35, "길이_cm": 42,
         "위험도": "고", "AI신뢰도": 0.94, "탐지방법": "드론스캔", "기준": "0.2mm 초과"},
        {"위치": "마포B동 지하 1층 천장", "유형": "누수흔적", "폭_mm": 0.12, "길이_cm": 18,
         "위험도": "중", "AI신뢰도": 0.88, "탐지방법": "앱업로드", "기준": "습윤면적 200cm²"},
        {"위치": "서초E동 외벽 전면", "유형": "드라이비트화재취약", "폭_mm": 0.0, "길이_cm": 850,
         "위험도": "고", "AI신뢰도": 0.91, "탐지방법": "드론스캔", "기준": "KFS 화재안전기준"},
        {"위치": "노원C동 옥상 방수층", "유형": "박리손상", "폭_mm": 2.10, "길이_cm": 95,
         "위험도": "고", "AI신뢰도": 0.89, "탐지방법": "드론스캔", "기준": "0.5mm 초과"},
        {"위치": "강남A동 계단실 2층", "유형": "수평균열", "폭_mm": 0.08, "길이_cm": 11,
         "위험도": "저", "AI신뢰도": 0.79, "탐지방법": "앱업로드", "기준": "0.2mm 미만"},
        {"위치": "강서D동 지하주차장", "유형": "누수흔적", "폭_mm": 0.45, "길이_cm": 67,
         "위험도": "중", "AI신뢰도": 0.86, "탐지방법": "드론스캔", "기준": "0.2mm 초과"},
        {"위치": "마포B동 외벽 5층 동측", "유형": "표면박락", "폭_mm": 0.55, "길이_cm": 28,
         "위험도": "중", "AI신뢰도": 0.83, "탐지방법": "앱업로드", "기준": "0.5mm 초과"},
        {"위치": "구미A동 외벽 전체", "유형": "드라이비트화재취약", "폭_mm": 0.0, "길이_cm": 1200,
         "위험도": "고", "AI신뢰도": 0.93, "탐지방법": "드론스캔", "기준": "KFS 화재안전기준"},
    ]
    return pd.DataFrame(items)

def make_billing_data():
    """관리비 고지서 데이터 (RPA 자동화 대상)"""
    rows = []
    for cpx in ALL_COMPLEXES:
        세대수 = int(cpx.split("세대)")[0].split(", ")[-1])
        for 동 in range(1, 4):
            for 층 in range(2, 8):
                for 호 in range(1, 5):
                    rows.append({
                        "단지": cpx[:15] + "..",
                        "호수": f"{동}동{층}층{호}호",
                        "관리비_만원": round(random.uniform(8, 25), 1),
                        "전기료_만원": round(random.uniform(2, 8), 1),
                        "수도료_만원": round(random.uniform(1, 4), 1),
                        "청구월": "2026-04",
                        "발행상태": random.choice(["자동발행완료", "자동발행완료", "자동발행완료", "오류확인필요"]),
                        "발행일시": (datetime.now() - timedelta(hours=random.randint(0, 48))).strftime("%Y-%m-%d %H:%M"),
                    })
    return pd.DataFrame(rows)

def make_contract_data():
    """계약 만료 알림 데이터 (RPA 100% 자동화)"""
    rows = []
    for i in range(40):
        expire_days = random.randint(-30, 180)
        rows.append({
            "입주민번호": f"T-{1000+i}",
            "단지": random.choice(ALL_COMPLEXES)[:15] + "..",
            "호수": f"{random.randint(1,3)}동{random.randint(2,7)}층{random.randint(1,4)}호",
            "계약만료일": (date.today() + timedelta(days=expire_days)).strftime("%Y-%m-%d"),
            "잔여일수": expire_days,
            "알림상태": "발송완료" if expire_days < 60 else "예정",
            "자동알림": "RPA 자동발송",
            "갱신의향": random.choice(["갱신희망", "미정", "퇴거예정"]),
        })
    return pd.DataFrame(rows)

def make_milage_data():
    """클린하우스 마일리지 데이터"""
    rows = []
    for i in range(50):
        rows.append({
            "세대": f"{random.randint(1,3)}동{random.randint(2,7)}층{random.randint(1,4)}호",
            "단지": random.choice(ALL_COMPLEXES)[:15] + "..",
            "마일리지": random.randint(0, 1500),
            "등급": random.choice(["골드", "실버", "브론즈", "일반"]),
            "자체점검횟수": random.randint(0, 12),
            "앱사용여부": random.choice(["사용", "사용", "미사용"]),
            "인센티브_만원": random.choice([0, 0, 5, 10, 20]),
        })
    return pd.DataFrame(rows)

def make_failure_forecast():
    """고장 예측 데이터 (Vision 2030 ML)"""
    months = [(datetime.now() + timedelta(days=30*i)).strftime("%Y-%m") for i in range(12)]
    rows = []
    for cpx in ALL_COMPLEXES[:4]:
        built_year = int(cpx.split("준공: ")[1][:4])
        age = 2026 - built_year
        base = age / 5
        for m, month in enumerate(months):
            rows.append({
                "단지": cpx[:16] + "..",
                "예측월": month,
                "예상고장건수": max(0, round(base + m * 0.3 + np.random.normal(0, 0.5))),
                "AI적용전": max(0, round(base * 1.3 + m * 0.4 + np.random.normal(0, 0.5))),
                "신뢰구간_하": max(0, round(base + m * 0.3 - 1.2)),
                "신뢰구간_상": round(base + m * 0.3 + 1.2),
            })
    return pd.DataFrame(rows)

def make_ai_pipeline_samples():
    """AI 데이터 파이프라인 샘플 데이터셋 (RAW → 학습 → 모델 → 결과 → 활용 → 효과)"""
    samples = [
        # ── 카테고리 1: 비전 AI — 드론·앱 시설물 손상 이미지 (10건) ──
        {"ID":"P-001","분류":"비전AI-이미지","RAW데이터":"드론 촬영 외벽 이미지 (4K, 강남A동 3층 북측)","학습데이터":"512×512 패치 분할 + 균열 마스크 라벨링 (COCO format)","AI모델":"Y-MaskNet (Mask R-CNN, ResNet-101 백본, F1=0.97)","결과":"수직균열 탐지: 폭 0.35mm, 길이 42cm, 신뢰도 94%","활용":"즉시 구조전문가 요청 → 48h 내 긴급 보수 지시","효과":"대형 구조사고 사전 차단, 보수비 70% 절감 (조기 발견)"},
        {"ID":"P-002","분류":"비전AI-이미지","RAW데이터":"입주민 앱 업로드 지하층 천장 사진 (마포B동)","학습데이터":"습윤 영역 세그멘테이션 마스크 + 면적 라벨 (200cm² 기준)","AI모델":"Y-MaskNet (Instance Segmentation, IoU=0.91)","결과":"누수흔적 탐지: 습윤면적 312cm², 신뢰도 88%","활용":"3일 내 현장 점검 예약 + 배관 보수팀 자동 배정","효과":"누수 확대 방지, 하자보수 비용 45% 절감"},
        {"ID":"P-003","분류":"비전AI-이미지","RAW데이터":"드론 스캔 외벽 전면 (서초E동, 열화상 포함)","학습데이터":"드라이비트 외장재 영역 바운딩박스 + KFS 화재안전기준 매핑","AI모델":"Y-MaskNet + Thermal Fusion (KFS 기준 분류기)","결과":"드라이비트 화재취약 구간: 850cm, 위험도 고, 신뢰도 91%","활용":"즉시 긴급 점검 + 30일 내 불연재 교체 계획 수립","효과":"화재 사망사고 원천 차단, 보험료 20% 절감"},
        {"ID":"P-004","분류":"비전AI-이미지","RAW데이터":"드론 촬영 옥상 방수층 (노원C동, RGB+NIR)","학습데이터":"박리·부풀음 영역 폴리곤 라벨 + 깊이(mm) 회귀 타겟","AI모델":"Y-MaskNet (Multi-task: 세그멘테이션 + 깊이 회귀)","결과":"박리손상 탐지: 폭 2.1mm, 면적 95cm², 신뢰도 89%","활용":"옥상 방수 전면 재시공 지시 + 우기 전 완료 목표","효과":"누수로 인한 실내 피해 예방, 세대 이주 비용 0원"},
        {"ID":"P-005","분류":"비전AI-이미지","RAW데이터":"앱 업로드 계단실 벽면 사진 (강남A동 2층)","학습데이터":"미세균열 어노테이션 (0.05~0.2mm 구간, Antigravity 보정)","AI모델":"Y-MaskNet + Antigravity 오탐보정 엔진","결과":"수평균열 0.08mm 탐지 (기준 미만), 위험도 저, 신뢰도 79%","활용":"정기점검 유지, 6개월 후 재촬영 예약","효과":"불필요한 긴급출동 방지 (오탐 0건), 인건비 절감"},
        {"ID":"P-006","분류":"비전AI-이미지","RAW데이터":"드론 촬영 지하주차장 천장 (강서D동, LED 조명 보정)","학습데이터":"누수 패턴 5종 분류 라벨 (침출수/결로/배관/방수불량/정상)","AI모델":"Y-MaskNet (5-class Classification, Acc=0.93)","결과":"배관 누수 탐지: 폭 0.45mm, 길이 67cm, 신뢰도 86%","활용":"배관 교체 작업지시 + 주차장 일부 통제 안내","효과":"주차장 구조체 열화 방지, 장기 유지비 35% 절감"},
        {"ID":"P-007","분류":"비전AI-이미지","RAW데이터":"앱 업로드 외벽 표면 사진 (마포B동 5층 동측)","학습데이터":"박락 영역 마스크 + 깊이·면적 복합 라벨","AI모델":"Y-MaskNet (Surface Defect Detection, mAP=0.89)","결과":"표면박락 탐지: 깊이 0.55mm, 면적 28cm², 신뢰도 83%","활용":"30일 내 외벽 부분 보수 계획 수립","효과":"박락 확대→낙하물 사고 예방, 입주민 안전 확보"},
        {"ID":"P-008","분류":"비전AI-이미지","RAW데이터":"드론 촬영 외벽 전체 (구미A동, 파노라마 스티칭)","학습데이터":"대면적 드라이비트 영역 세그멘테이션 + 두께 추정 라벨","AI모델":"Y-MaskNet + Panorama Stitcher (1200cm 연속 탐지)","결과":"드라이비트 화재취약 1200cm 전면 탐지, 신뢰도 93%","활용":"긴급 불연재 교체 공사 발주 + 임시 소화설비 배치","효과":"대규모 화재 원천 차단, 보험사 특약 할인 확보"},
        {"ID":"P-009","분류":"비전AI-이미지","RAW데이터":"드론 야간 열화상 촬영 (서초E동, FLIR 카메라)","학습데이터":"열분포 이상 영역 히트맵 라벨 + 단열 불량 등급","AI모델":"Thermal-MaskNet (열화상 전용 세그멘테이션)","결과":"단열 불량 구간 3개소 탐지, 열손실 15% 이상, 신뢰도 87%","활용":"동절기 전 단열 보강 공사 계획 수립","효과":"난방비 12% 절감, 결로·곰팡이 민원 감소"},
        {"ID":"P-010","분류":"비전AI-이미지","RAW데이터":"입주민 앱 연속 촬영 (동일 균열 3개월 추적, 강남A동)","학습데이터":"시계열 균열폭 변화 데이터 (0.15→0.22→0.35mm)","AI모델":"Y-MaskNet + LSTM 시계열 진행 예측","결과":"균열 성장률 0.07mm/월, 6개월 후 0.77mm 예측, 신뢰도 92%","활용":"구조 안전성 긴급 평가 요청 + 예방 보수 즉시 시행","효과":"구조적 위험 도달 前 선제 조치, 대형사고 원천 차단"},

        # ── 카테고리 2: IoT 센서·LiDAR 데이터 (8건) ──
        {"ID":"P-011","분류":"IoT-센서","RAW데이터":"온도센서 시계열 (마포B동 3층, 30일×24h=720포인트)","학습데이터":"정상/이상 라벨링 (30°C 초과 = 이상, 시간대별 가중치)","AI모델":"AutoEncoder 이상탐지 (Reconstruction Error 기반)","결과":"2026-04-04 09:05 온도 32.1°C 이상 감지 (기준 30°C)","활용":"환기 권고 문자 자동 발송 + HVAC 점검 예약","효과":"열사병·화재 위험 사전 차단, 에너지 효율 8% 개선"},
        {"ID":"P-012","분류":"IoT-센서","RAW데이터":"CO 농도센서 시계열 (마포B동 지하, 실시간 1분 간격)","학습데이터":"급등 패턴 라벨 (10ppm 초과 + 상승률 > 2ppm/min = 긴급)","AI모델":"LSTM 시계열 예측 + Anomaly Score 산출","결과":"2026-04-07 02:14 CO 16.2ppm 급등 (기준 10ppm, 62% 초과)","활용":"담당자 긴급 문자 + 환기팀 즉시 출동 + 입주민 대피 안내","효과":"CO 중독 사고 사전 차단, 인명피해 0건 유지"},
        {"ID":"P-013","분류":"IoT-센서","RAW데이터":"진동센서 가속도 (강남A동 지하, 3축 100Hz 샘플링)","학습데이터":"진동 크기·주파수 스펙트럼 특징 추출 + 위험등급 라벨","AI모델":"Random Forest 분류기 (정상/주의/위험/긴급 4등급)","결과":"2026-04-06 18:33 진동 0.85g 감지 (기준 0.5g, 70% 초과)","활용":"구조팀 긴급 점검 요청 + 인접 세대 안전 점검","효과":"구조물 피로파괴 조기 경보, 붕괴 위험 사전 차단"},
        {"ID":"P-014","분류":"IoT-센서","RAW데이터":"습도센서 데이터 (노원C동 옥상층, 15분 간격 기록)","학습데이터":"습도-누수 상관 모델 학습 데이터 (70% 초과 시 누수 확률 매핑)","AI모델":"Gradient Boosting 회귀 (누수 확률 예측)","결과":"2026-04-05 14:21 습도 78.4% (기준 70%), 누수 확률 73%","활용":"누수 모니터링 강화 + 3일 내 점검 자동 예약","효과":"누수 확대 전 조기 탐지, 수리비 50% 절감"},
        {"ID":"P-015","분류":"IoT-LiDAR","RAW데이터":"LiDAR 3D 점군 데이터 (강남A동 외벽, 1억 포인트)","학습데이터":"포인트클라우드 → 메시 변환, 균열·변형 영역 3D 라벨링","AI모델":"PointNet++ (3D 세그멘테이션, mIoU=0.88)","결과":"외벽 변형 3개소 탐지: 최대 변위 12mm, 기울기 0.3°","활용":"Digital Twin 3D 모델 갱신 + 구조 안전 평가 연계","효과":"2D 이미지 대비 탐지율 15% 향상, 사각지대 제거"},
        {"ID":"P-016","분류":"IoT-센서","RAW데이터":"전력 사용량 스마트미터 (전 단지, 1시간 간격)","학습데이터":"세대별 전력 패턴 클러스터링 + 이상 소비 라벨","AI모델":"K-Means 클러스터링 + Isolation Forest 이상탐지","결과":"서초E동 302호 전력 5.8kWh 이상 소비 (평균 대비 240%)","활용":"전기안전점검 자동 예약 + 누전 가능성 안내","효과":"전기 화재 예방, 에너지 비용 15% 절감"},
        {"ID":"P-017","분류":"IoT-LiDAR","RAW데이터":"LiDAR SLAM 3D 맵핑 (노원C동 옥상 전체, 월 1회 스캔)","학습데이터":"시계열 3D 변위맵 (이전 스캔 대비 차분, mm 단위)","AI모델":"ICP 정합 + Change Detection CNN","결과":"옥상 방수층 부풀음 2개소 신규 탐지 (면적 증가 +18%)","활용":"방수층 보수 우선순위 자동 갱신 + 우기 전 긴급 보수","효과":"옥상 누수 사전 차단, 실내 피해 비용 0원"},
        {"ID":"P-018","분류":"IoT-센서","RAW데이터":"복합 센서 융합 (온도+습도+CO+진동, 5개 센서 동시 기록)","학습데이터":"5차원 센서 융합 시계열 + 복합 이상 시나리오 라벨","AI모델":"Multivariate LSTM-Attention (5센서 융합 예측)","결과":"복합 이상 패턴 감지: 습도↑+온도↑+CO↑ 동시 발생 (화재 전조)","활용":"소방서 자동 신고 + 층별 대피 안내 + 스프링클러 사전 점검","효과":"화재 초기 대응 시간 70% 단축, 인명·재산 피해 최소화"},

        # ── 카테고리 3: 공공임대 민원 데이터 (6건) ──
        {"ID":"P-019","분류":"민원-NLP","RAW데이터":"입주민 민원 텍스트 (CM-2026-1023, '3층 화장실 천장 물방울')","학습데이터":"민원 텍스트 → 유형(7종) + 위험도(고/중/저) + 위치 NER 라벨","AI모델":"KoBERT 분류기 (7종 유형 분류, Acc=0.92)","결과":"자동 분류: 유형=누수, 위험도=중, 위치=3층 화장실, 신뢰도 0.89","활용":"배관팀 자동 배정 (이점검) + 3일 내 현장 방문 예약","효과":"민원 처리시간 3일→1일 (67% 단축), 입주민 만족도 20%↑"},
        {"ID":"P-020","분류":"민원-NLP","RAW데이터":"민원 텍스트 (CM-2026-1045, '외벽 금 가고 조각 떨어짐 위험')","학습데이터":"긴급 키워드 가중치 + 위험도 매핑 (떨어짐→고위험)","AI모델":"KoBERT + Rule-based 하이브리드 (키워드 부스팅)","결과":"자동 분류: 유형=균열·구조손상, 위험도=고, 신뢰도 0.94","활용":"즉시 구조전문가 배정 + 입주민 안전 문자 발송","효과":"고위험 민원 누락 0건, 즉시 대응으로 2차 사고 방지"},
        {"ID":"P-021","분류":"민원-분석","RAW데이터":"6개월 민원 이력 데이터 (480건, 7개 단지 통합)","학습데이터":"단지×유형×월별 빈도 집계 + 계절·노후도 피처 결합","AI모델":"XGBoost 민원 발생 예측 (월별 예측, RMSE=2.1건)","결과":"노원C동 다음달 누수 민원 12건 예측 (현재 8건 대비 +50%)","활용":"선제적 누수 점검 집중 배치 + 예비 자재 확보","효과":"민원 발생 자체를 30% 감소, 사후 대응→사전 예방 전환"},
        {"ID":"P-022","분류":"민원-감성","RAW데이터":"민원 텍스트 감성 분석용 데이터 (긍정/부정/중립)","학습데이터":"민원 텍스트 + 만족도 조사 결과 매핑 (5점 척도)","AI모델":"KoBERT 감성분석 (3분류, F1=0.87)","결과":"부정 감성 65% → 처리 후 긍정 전환율 78%","활용":"부정 감성 높은 민원 우선 처리 + 만족도 추적","효과":"입주민 만족도 20% 향상, 분쟁 건수 40% 감소"},
        {"ID":"P-023","분류":"민원-이미지","RAW데이터":"민원 첨부 사진 (입주민 촬영, 저화질·다양한 각도)","학습데이터":"사진→손상유형 매핑 (균열/누수/곰팡이/파손/기타)","AI모델":"EfficientNet-B3 분류기 (5종, Top-1 Acc=0.86)","결과":"첨부 사진에서 곰팡이 자동 탐지 + 면적 추정 12cm²","활용":"환경팀 자동 배정 + 실내 환기 개선 안내 문자","효과":"사진 기반 자동 분류로 수동 판독 시간 80% 절감"},
        {"ID":"P-024","분류":"민원-예측","RAW데이터":"민원 처리 이력 (접수→완료 전 과정 타임스탬프)","학습데이터":"처리 단계별 소요시간 + 담당자·유형·위험도 피처","AI모델":"LightGBM 처리시간 예측 (MAE=0.3일)","결과":"CM-2026-1067 예상 처리완료: 2.1일 (목표 1일 대비 지연 예측)","활용":"추가 인력 자동 배정 + 입주민 지연 안내 문자","효과":"처리 지연 사전 감지, SLA 준수율 95%→98% 향상"},

        # ── 카테고리 4: Digital Twin 데이터 (6건) ──
        {"ID":"P-025","분류":"DigitalTwin-3D","RAW데이터":"BIM 설계 도면 + LiDAR 현황 스캔 (강남A동 전체)","학습데이터":"설계 vs 현황 차분 데이터 + 변형 유형 라벨 (침하/기울기/균열)","AI모델":"3D Point Cloud Matching + Anomaly Detection","결과":"1층 기둥 기울기 0.15° 감지 (설계 대비), 침하 8mm","활용":"Digital Twin 실시간 갱신 + 구조 안전 경보 생성","효과":"설계 도면 기반 정밀 비교로 육안 점검 불가 영역 커버"},
        {"ID":"P-026","분류":"DigitalTwin-시뮬","RAW데이터":"세종대 비선형 FEM 구조해석 입력 데이터 (하중·재료·경계조건)","학습데이터":"FEM 해석 결과 + 실측 변위 데이터 보정 세트","AI모델":"Physics-Informed Neural Network (PINN, FEM 대리모델)","결과":"10분 내 구조 안전성 시뮬레이션 완료 (기존 FEM 8시간)","활용":"긴급 상황 시 실시간 구조 안전 판정 + 대피 의사결정","효과":"구조 해석 시간 98% 단축, 긴급 대응 의사결정 실시간화"},
        {"ID":"P-027","분류":"DigitalTwin-에너지","RAW데이터":"IoT 에너지 사용 데이터 + 기상 데이터 (12개월 연속)","학습데이터":"시간대별 에너지 소비 패턴 + 외기온·일사량 결합","AI모델":"GBR 에너지 예측 모델 (R²=0.94)","결과":"다음 달 전력비 예측: 892만원 (AI 최적화 시 743만원, -17%)","활용":"HVAC 운전 스케줄 자동 최적화 + 야간 전력 전환","효과":"연간 에너지 비용 15% 절감 (약 1,800만원/년)"},
        {"ID":"P-028","분류":"DigitalTwin-노후","RAW데이터":"KALIS-FMS 30년 안전진단 이력 + 일송건축 설계도면","학습데이터":"경과년수별 노후도 진행 곡선 + 보수 이력 반영","AI모델":"Antigravity 엔진 (3중 교차검증: 이력+설계+FEM)","결과":"강남A동 구조 건전도 44.6점, 5년 후 35.2점 예측","활용":"장기 보수 계획 수립 + 예산 선제 확보 요청","효과":"노후 시설물 수명 10년 연장, 재건축 비용 지연 효과"},
        {"ID":"P-029","분류":"DigitalTwin-배관","RAW데이터":"지하 배관 도면 + GPR 탐사 데이터 + 누수 이력","학습데이터":"배관 재질·경과년수·토질 조건별 파손 확률 라벨","AI모델":"Survival Analysis (Cox 비례위험 모델)","결과":"마포B동 급수관 3년 내 파손 확률 42% (교체 권고)","활용":"배관 교체 우선순위 자동 결정 + 공사 일정 최적화","효과":"긴급 파열 사고 방지, 단수 피해 0건 목표"},
        {"ID":"P-030","분류":"DigitalTwin-화재","RAW데이터":"드라이비트 외벽 3D 모델 + 화재 시뮬레이션 입력","학습데이터":"외벽재질·면적·층수별 화재 확산 시뮬레이션 결과셋","AI모델":"FDS(Fire Dynamics Simulator) + ML 대리모델","결과":"서초E동 화재 시 3분 내 3개층 확산 예측, 대피 경로 생성","활용":"소방 시뮬레이션 결과 FMS 등록 + 대피 훈련 계획 수립","효과":"화재 대응 시간 50% 단축, 인명피해 최소화 전략 확보"},

        # ── 카테고리 5: 실시간 이상 징후 데이터 (5건) ──
        {"ID":"P-031","분류":"이상징후-복합","RAW데이터":"5개 센서 동시 이상 (온도↑+습도↑+CO↑, 마포B동 지하)","학습데이터":"복합 이상 시나리오 패턴 라벨 (화재전조/누수/설비고장)","AI모델":"Multivariate Anomaly Detector (Attention-LSTM)","결과":"화재 전조 패턴 감지: 위험도 0.91, 소방 대응 권고","활용":"자동 소방서 연계 + 층별 대피 안내 + 스프링클러 점검","효과":"화재 사전 차단율 94%, 인명 피해 0건 유지"},
        {"ID":"P-032","분류":"이상징후-진동","RAW데이터":"인접 공사현장 진동 연속 기록 (강남A동, 72시간)","학습데이터":"진동 크기·지속시간·주파수별 구조물 영향 라벨","AI모델":"FFT + Random Forest (구조물 영향 4등급 분류)","결과":"진동 누적 에너지 기준 초과, 구조물 피로도 주의 단계","활용":"공사현장 진동 저감 요청 + 구조물 정밀 점검 예약","효과":"공사 진동으로 인한 구조 손상 사전 차단"},
        {"ID":"P-033","분류":"이상징후-전력","RAW데이터":"전력 사용 패턴 급변 (서초E동, 심야 3시 이상 부하)","학습데이터":"시간대별 전력 패턴 프로파일 + 이상 유형 라벨","AI모델":"Isolation Forest + DBSCAN (이상 패턴 군집화)","결과":"심야 전력 5.8kWh 감지 (평균 2.1kWh 대비 276% 초과)","활용":"전기안전점검 자동 예약 + 누전 차단기 원격 모니터링","효과":"전기 화재 사전 예방, 감전 사고 위험 원천 차단"},
        {"ID":"P-034","분류":"이상징후-가스","RAW데이터":"가스 감지센서 이벤트 로그 (구미A동, 0.1초 간격)","학습데이터":"가스 농도 급등 패턴 + 원인 분류 (배관누출/환기불량/오작동)","AI모델":"1D-CNN 시계열 분류기 (3종 원인, F1=0.91)","결과":"배관 미세 누출 패턴 감지: 농도 0.3% (경보 기준 0.5% 미만)","활용":"사전 경고 + 가스 점검팀 48h 내 방문 예약","효과":"가스 폭발 사고 사전 차단, 주기적 예방 점검 자동화"},
        {"ID":"P-035","분류":"이상징후-수위","RAW데이터":"지하 집수정 수위센서 (강서D동, 5분 간격 기록)","학습데이터":"수위 상승 속도 + 강우 데이터 결합, 침수 위험도 라벨","AI모델":"ARIMA + ML 하이브리드 (수위 예측, 6시간 선행)","결과":"6시간 후 수위 경고 수준 도달 예측 (집중호우 시)","활용":"양수 펌프 사전 가동 + 지하주차장 차량 이동 안내","효과":"지하 침수 피해 사전 차단, 차량 침수 보상 비용 0원"},

        # ── 카테고리 6: 선제 탐지 예시 데이터 (5건) ──
        {"ID":"P-036","분류":"선제탐지-균열","RAW데이터":"동일 균열 6개월 추적 이미지 시리즈 (월 1회 촬영)","학습데이터":"균열폭 시계열 [0.10, 0.13, 0.18, 0.22, 0.28, 0.35mm]","AI모델":"LSTM 성장 예측 + 위험 도달 시점 추정","결과":"3개월 후 0.5mm 도달 예측 (정밀안전진단 기준 초과)","활용":"정밀안전진단 기준 초과 前 선제 보수 지시","효과":"정밀안전진단 비용 절감 + 대형 보수 회피 (비용 70%↓)"},
        {"ID":"P-037","분류":"선제탐지-배관","RAW데이터":"배관 IoT 유량·압력 센서 (마포B동, 30일 연속)","학습데이터":"유량-압력 상관관계 변화 패턴 + 누수 전조 라벨","AI모델":"PCA + Hotelling T² 통계적 공정 관리","결과":"유량-압력 상관관계 이탈 감지 (누수 전조 확률 78%)","활용":"배관 내시경 점검 선제 예약 + 교체 자재 확보","효과":"배관 파열 전 선제 교체, 긴급 단수 0건 유지"},
        {"ID":"P-038","분류":"선제탐지-외벽","RAW데이터":"계절별 외벽 열화상 데이터 (겨울 동결·해동 4회 기록)","학습데이터":"동결-해동 사이클 횟수 + 균열 성장 상관 데이터","AI모델":"계절 취약 패턴 학습 (Seasonal ARIMA + 물리 모델)","결과":"겨울철 동결-해동 10회 이상 구간 → 봄 균열 확대 87% 예측","활용":"동절기 종료 직후 취약 구간 집중 점검 자동 스케줄링","효과":"계절적 손상 패턴 선제 대응, 봄철 긴급 보수 건수 50%↓"},
        {"ID":"P-039","분류":"선제탐지-승강기","RAW데이터":"승강기 운행 로그 + 진동·소음 센서 (노원C동, 3대)","학습데이터":"고장 전 7일 이상 패턴 + 정상 운행 베이스라인","AI모델":"Predictive Maintenance (XGBoost, 7일 선행 예측)","결과":"2호기 브레이크 패드 마모 예측 (잔여 수명 14일)","활용":"정기 점검일 앞당김 + 부품 선제 발주","효과":"승강기 갑작스러운 정지 사고 0건, 입주민 불편 최소화"},
        {"ID":"P-040","분류":"선제탐지-방수","RAW데이터":"옥상 방수층 IoT 수분센서 + 기상청 강우 예보","학습데이터":"방수층 수분 침투 속도 + 강우량·기온 상관 모델","AI모델":"Weather-Aware 방수 성능 예측 (ML + 기상 API)","결과":"다음 주 집중호우 시 옥상 방수 실패 확률 65%","활용":"우기 전 방수 보수 긴급 시행 + 임시 방수 시트 설치","효과":"옥상 누수로 인한 실내 피해 원천 차단 (연 5건→0건)"},

        # ── 카테고리 7: RPA 행정 자동화 데이터 (7건) ──
        {"ID":"P-041","분류":"RPA-관리비","RAW데이터":"504세대 관리비 원장 (전기·수도·공용·수선충당금 항목)","학습데이터":"세대별 청구 규칙 매핑 + 이상 청구 패턴 학습","AI모델":"Rule Engine + Anomaly Detection (이상 청구 자동 검출)","결과":"504세대 고지서 자동 생성 완료 (오류 검출 12건 자동 보정)","활용":"80% 자동 발행 + 20% 오류 건 담당자 확인 큐 전달","효과":"고지서 발행 시간 8시간→1.5시간 (81% 단축)"},
        {"ID":"P-042","분류":"RPA-계약","RAW데이터":"40건 임대차 계약 만료 데이터 (만료일·갱신의향·연체이력)","학습데이터":"갱신 확률 예측용 피처셋 (잔여일수·연체·만족도)","AI모델":"Logistic Regression (갱신 확률 예측, AUC=0.89)","결과":"60일 내 만료 15건 중 퇴거예정 3건 자동 식별","활용":"100% 자동 알림 발송 + 퇴거 예정 건 대기자 매칭","효과":"계약 갱신 알림 누락 0건, 공실 기간 평균 15일 단축"},
        {"ID":"P-043","분류":"RPA-점검","RAW데이터":"7개 단지 시설물 대장 + 노후도 점수 + 점검 이력","학습데이터":"노후도→점검주기 매핑 규칙 + 계절·기상 보정 가중치","AI모델":"규칙 기반 스케줄러 + ML 우선순위 최적화","결과":"7개 단지 월간 점검 일정 자동 생성 (긴급 3·일반 2·예정 2)","활용":"90% 자동 스케줄링 + 담당자 앱 자동 할당","효과":"점검 업무 시간 50% 단축, 점검 누락 0건"},
        {"ID":"P-044","분류":"RPA-민원배정","RAW데이터":"민원 접수 데이터 (유형·위험도·위치·담당자 이력)","학습데이터":"담당자별 전문분야·처리속도·현재 업무량 데이터","AI모델":"Assignment Optimization (Hungarian Algorithm + ML)","결과":"최적 담당자 자동 배정: 김관리(누수 전문, 잔여 업무 2건)","활용":"75% 자동 배정 + 고위험 건 팀장 확인 후 배정","효과":"민원 배정 시간 2시간→5분, 전문가 매칭 정확도 90%"},
        {"ID":"P-045","분류":"RPA-보고서","RAW데이터":"점검 결과 + 법적 근거 + 권고 조치 (비정형 텍스트)","학습데이터":"완성된 점검 보고서 템플릿 + 법령 DB (RAG 인덱싱)","AI모델":"LLM + RAG (법령 자동 검색, 보고서 자동 생성)","결과":"AI 점검 보고서 초안 자동 생성 (3시간→36분, 80% 단축)","활용":"법무법인 수호 자문 포맷 적용 → 공문서 효력 확보","효과":"보고서 작성 비용 80% 절감, 법적 리스크 제거"},
        {"ID":"P-046","분류":"RPA-고지","RAW데이터":"관리비 연체 현황 + 세대별 납부 이력 (24개월)","학습데이터":"연체 패턴 + 납부 확률 예측 피처 (소득·연체횟수·계절)","AI모델":"Gradient Boosting (연체 확률 예측, AUC=0.85)","결과":"다음 달 연체 예상 세대 23건 식별 (연체 확률 >60%)","활용":"사전 납부 안내 문자 + 분납 상담 자동 연결","효과":"연체율 15%→8% 감소, 관리비 수납률 92%→97%"},
        {"ID":"P-047","분류":"RPA-에너지","RAW데이터":"공용부 전력 사용 데이터 (복도·주차장·엘리베이터)","학습데이터":"시간대별 사용 패턴 + 절전 가능 구간 라벨","AI모델":"Time-Series Optimization (RL 기반 HVAC 제어)","결과":"야간 공용부 조명 50% 감광 + HVAC 최적 스케줄 생성","활용":"BMS 자동 제어 연동 + 월간 절감 보고서 자동 생성","효과":"공용부 전력비 연 1,200만원 절감 (18% 감소)"},

        # ── 카테고리 8: 예방조치 데이터 (5건) ──
        {"ID":"P-048","분류":"예방조치-구조","RAW데이터":"XAI 위험도 스코어 88점 (강남A동, 7개 지표 종합)","학습데이터":"7개 예방 지표 가중합 + SHAP 기여도 분해","AI모델":"XAI 위험도 스코어링 엔진 v2.0 (세종대 공동개발)","결과":"즉시 정비 지시: 경과년수 30%↑ + IoT이상 20%↑ + 균열성장 18%↑","활용":"48h 내 긴급 정비 지시서 자동 생성 + 담당자 앱 알림","효과":"사고 전환 차단율 94%, 대형 사고 0건 유지"},
        {"ID":"P-049","분류":"예방조치-화재","RAW데이터":"드라이비트 탐지 결과 + KFS 화재안전기준 매핑","학습데이터":"외벽재질·면적·층수 → 화재 위험등급 학습 데이터","AI모델":"Multi-criteria Decision (화재위험 종합 스코어링)","결과":"서초E동 화재위험 등급 A (즉시 조치), 구미A동 등급 B","활용":"불연재 교체 공사 발주 + 임시 소화설비 설치 지시","효과":"화재 사망사고 원천 차단 + 건축법 기준 충족"},
        {"ID":"P-050","분류":"예방조치-누수","RAW데이터":"누수 이력 + 배관 노후도 + IoT 습도 이상 이벤트 종합","학습데이터":"복합 요인 결합 → 누수 재발 확률 예측 피처","AI모델":"Ensemble (RF + XGBoost + LightGBM, Stacking)","결과":"마포B동 지하 누수 재발 확률 73% (3개월 내)","활용":"배관 전면 교체 결정 + 공사 일정·예산 확보","효과":"반복 누수 원천 차단, 수선충당금 효율적 집행"},
        {"ID":"P-051","분류":"예방조치-지반","RAW데이터":"GPR 탐사 데이터 + InSAR 침하 속도맵 + 지하수위","학습데이터":"다변량 시계열 + 지반침하 이벤트 라벨 (서울시 5년)","AI모델":"STL-XGBoost 융합 예측 (침하 확률 0~1)","결과":"노원C동 주변 도로 30일 내 침하 확률 0.68 (고위험)","활용":"GPR 즉시 확인 탐사 + 도로 통행 제한 검토","효과":"지반침하 사고 사전 차단, 인명·재산 피해 원천 방지"},
        {"ID":"P-052","분류":"예방조치-종합","RAW데이터":"7개 단지 전체 AI 위험도 스코어 종합 현황","학습데이터":"단지별 위험도 시계열 추이 + 보수 이력 효과 분석","AI모델":"Portfolio Risk Management (전사 위험도 최적화)","결과":"이번 달 고위험 3개 단지 · 중위험 2개 · 정상 2개","활용":"예산 우선 배분 최적화 + 월간 경영 보고서 자동 생성","효과":"한정된 예산으로 최대 위험 감소 효과 달성 (ROI 340%)"},

        # ── 카테고리 9: 대시보드 분석 데이터 (3건) ──
        {"ID":"P-053","분류":"대시보드-KPI","RAW데이터":"전체 플랫폼 운영 데이터 (7개 단지, 2,847세대, 실시간)","학습데이터":"KPI 집계 규칙 + 목표 대비 달성률 자동 산출","AI모델":"실시간 집계 엔진 + Trend Detection","결과":"점검완료율 94.2%, 민원처리 1.2일, AI탐지 정확도 93.1%","활용":"통합 대시보드 실시간 표출 + 경영진 일일 보고","효과":"데이터 기반 의사결정 체계 구축, 보고 시간 90% 절감"},
        {"ID":"P-054","분류":"대시보드-예측","RAW데이터":"Vision 2030 예측 모델 출력 (고장·에너지·공실 12개월)","학습데이터":"과거 실적 + AI 예측값 시계열 + 신뢰구간","AI모델":"Ensemble Forecasting (ML + 통계 모델 결합)","결과":"고장 30%↓, 에너지 15%↓, 공실 20%↓ 달성 경로 시각화","활용":"중장기 전략 수립 + 예산 배분 근거 자료","효과":"AI 기반 미래 예측으로 선제적 투자 의사결정 지원"},
        {"ID":"P-055","분류":"대시보드-ROI","RAW데이터":"AI 플랫폼 도입 전·후 비용 비교 데이터 (12개월)","학습데이터":"항목별 비용 절감 실적 + AI 기여도 분해","AI모델":"Cost-Benefit Analysis + Attribution Model","결과":"연간 총 절감: 관리비 1,350만원 + 에너지 1,800만원 + 보수비 4,200만원","활용":"투자 대비 효과 보고서 + 타 공사 확산 제안서","효과":"ROI 340%, 투자 회수 기간 8개월, LH 전국 확산 근거"},
    ]
    return pd.DataFrame(samples)

# 세션 캐시
if "초기화완료" not in st.session_state:
    st.session_state.iot_df         = make_iot_data()
    st.session_state.complaint_df   = make_complaints()
    st.session_state.inspection_df  = make_inspection()
    st.session_state.facility_df    = make_facilities()
    st.session_state.damage_df      = make_damage_detections()
    st.session_state.billing_df     = make_billing_data()
    st.session_state.contract_df    = make_contract_data()
    st.session_state.mileage_df     = make_milage_data()
    st.session_state.forecast_df    = make_failure_forecast()
    st.session_state.pipeline_df    = make_ai_pipeline_samples()
    st.session_state.초기화완료     = True

iot_df         = st.session_state.iot_df
complaint_df   = st.session_state.complaint_df
inspection_df  = st.session_state.inspection_df
facility_df    = st.session_state.facility_df
damage_df      = st.session_state.damage_df
billing_df     = st.session_state.billing_df
contract_df    = st.session_state.contract_df
mileage_df     = st.session_state.mileage_df
forecast_df    = st.session_state.forecast_df
pipeline_df    = st.session_state.pipeline_df

# ══════════════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1e3a5f,#2563eb);border-radius:10px;padding:16px;text-align:center;color:white;margin-bottom:12px;">
        <div style="font-size:22px;font-weight:900;">⚙ 에이톰-AX</div>
        <div style="font-size:10px;opacity:0.8;margin-top:4px;">공공주택 지능형 통합관리 플랫폼</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("", [
        "📊 통합 대시보드",
        "✈ 비전AI · 드론 정밀진단",
        "🤖 RPA 행정 자동화",
        "📋 AI 민원 관리",
        "📡 IoT · 디지털 트윈",
        "🛡 AI 사전 예방 정비",
        "🏅 클린하우스 마일리지",
        "🔮 Vision 2030 예측분석",
        "🧬 AI 데이터 파이프라인",
    ], label_visibility="collapsed",
    help="보고 싶은 메뉴를 클릭하세요 🖱️\n\n"
         "📊 통합 대시보드 — 전체 현황 한눈에\n"
         "✈ 비전AI — 드론·앱 이미지 AI 분석\n"
         "🤖 RPA — 관리비·계약·일정 자동화\n"
         "📋 민원 — 민원 접수·처리 현황\n"
         "📡 IoT — 센서 실시간 모니터링\n"
         "🛡 예방 정비 — AI 사고 예방 지시서\n"
         "🏅 마일리지 — 입주민 참여 인센티브\n"
         "🔮 Vision 2030 — 고장·에너지 예측\n"
         "🧬 AI 파이프라인 — 55개 학습데이터 명세"
    )

    st.divider()
    st.markdown("**수요처 선택**")
    demand_site = st.radio("", ["SH 서울주택도시공사", "경상북도개발공사"],
                           label_visibility="collapsed",
                           help="데이터를 조회할 공공주택 기관을 선택하세요 🏢\n\n"
                                "• SH공사: 서울 5개 단지 (강남·서초·마포·강서·노원)\n"
                                "• 경북개발공사: 경북 2개 단지 (구미·포항)")
    cpx_list = COMPLEXES_SH if "SH" in demand_site else COMPLEXES_GB
    selected_cpx = st.selectbox("단지 선택", cpx_list,
                                help="세부 데이터를 볼 단지를 고르세요 🏘️\n"
                                     "선택한 단지가 AI 분석·민원 접수의 기본 단지로 사용됩니다.")

    st.divider()
    st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.caption("국토교통부 AX-SPRINT 과제")
    st.caption("v1.0.3 · TRL 8 수준 · 현장실증 중")

# ══════════════════════════════════════════════════════
# PAGE 1: 통합 대시보드
# ══════════════════════════════════════════════════════
if page == "📊 통합 대시보드":
    st.title("📊 AX 기반 공공주택 안전·유지관리 통합 대시보드")
    st.caption(f"수요처: **{demand_site}** | 단지: **{selected_cpx[:20]}..** | 실시간 현황")

    # ── KPI 행 ──
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    kpi_data = [
        ("kpi-card",       "총 관리세대",      "2,847",     "7개 단지 합산"),
        ("kpi-card-green", "점검완료율",        "94.2%",     "목표: 95% ↑"),
        ("kpi-card-red",   "고위험 즉시조치",   "7건",       "균열·드라이비트"),
        ("kpi-card-amber", "평균 민원처리",     "1.2일",     "기존 3일 → 67%↓"),
        ("kpi-card",       "AI 탐지 정확도",    "93.1%",     "Y-MaskNet 기준"),
        ("kpi-card-green", "RPA 자동화율",      "81.5%",     "관리비·계약·점검"),
    ]
    for col, (cls, lbl, val, sub) in zip([k1,k2,k3,k4,k5,k6], kpi_data):
        with col:
            st.markdown(f"""
            <div class="{cls}">
                <div class="label">{lbl}</div>
                <div class="value">{val}</div>
                <div class="sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    # ── 실시간 알림 ──
    st.markdown('<div class="sh">🚨 실시간 위험 알림 (AI 자동 감지)</div>', unsafe_allow_html=True)
    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown('<div class="alert-critical">🔴 <b>[긴급] 서초E동 외벽</b> — 드라이비트 화재취약 850cm 탐지 (KFS 기준 초과) | 즉시 점검</div>', unsafe_allow_html=True)
        st.markdown('<div class="alert-critical">🔴 <b>[긴급] 강남A동 3층</b> — 수직균열 0.35mm (기준: 0.2mm) | 구조전문가 요청</div>', unsafe_allow_html=True)
    with a2:
        st.markdown('<div class="alert-warning">🟡 <b>[주의] 구미A동 외벽</b> — 드라이비트 화재취약 1200cm | 30일내 교체 권고</div>', unsafe_allow_html=True)
        st.markdown('<div class="alert-warning">🟡 <b>[주의] 마포B동 지하</b> — CO 16ppm 감지 (기준 10ppm) | 환기 조치</div>', unsafe_allow_html=True)
    with a3:
        st.markdown('<div class="alert-info">🔵 <b>[RPA] 관리비 고지서</b> — 4월분 2,847세대 자동발행 완료 (80% 자동화)</div>', unsafe_allow_html=True)
        st.markdown('<div class="alert-ok">🟢 <b>[정상] 강서D동</b> — 금일 드론 정기점검 완료 · 이상없음</div>', unsafe_allow_html=True)

    st.divider()

    # ── 차트 행 1 ──
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown('<div class="sh">📈 월별 손상 유형별 탐지 추이 (드론+앱 통합)</div>', unsafe_allow_html=True)
        months = [(datetime.now() - timedelta(days=30*i)).strftime("%Y-%m") for i in range(11,-1,-1)]
        fig = go.Figure()
        fig.add_bar(x=months, y=[random.randint(2,10) for _ in months], name="균열",         marker_color="#ef4444")
        fig.add_bar(x=months, y=[random.randint(1,6)  for _ in months], name="누수",         marker_color="#3b82f6")
        fig.add_bar(x=months, y=[random.randint(0,4)  for _ in months], name="드라이비트",   marker_color="#f97316")
        fig.add_bar(x=months, y=[random.randint(0,3)  for _ in months], name="박리·박락",    marker_color="#8b5cf6")
        fig.update_layout(barmode="stack", height=270, margin=dict(t=10,b=10),
                          legend=dict(orientation="h", y=1.05))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown('<div class="sh">🥧 민원 유형 분포</div>', unsafe_allow_html=True)
        tc = complaint_df["유형"].value_counts()
        fig2 = px.pie(values=tc.values, names=tc.index,
                      color_discrete_sequence=px.colors.qualitative.Set2, height=270,
                      hole=0.4)
        fig2.update_layout(margin=dict(t=10,b=10), legend=dict(font=dict(size=10)))
        st.plotly_chart(fig2, use_container_width=True)

    # ── 차트 행 2 ──
    c3, c4, c5 = st.columns(3)
    with c3:
        st.markdown('<div class="sh">🏗 단지별 노후도 점수</div>', unsafe_allow_html=True)
        nd = facility_df[["단지","노후도점수"]].copy()
        nd["단지"] = nd["단지"].str[:12]
        fig3 = px.bar(nd, x="노후도점수", y="단지", orientation="h",
                      color="노후도점수", color_continuous_scale="RdYlGn", height=270,
                      range_x=[0,100])
        fig3.update_layout(margin=dict(t=10,b=10), coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)
    with c4:
        st.markdown('<div class="sh">📋 민원 처리 단계별 현황</div>', unsafe_allow_html=True)
        sc = complaint_df["상태"].value_counts().reset_index()
        sc.columns = ["상태","건수"]
        color_map = {"접수":"#94a3b8","AI분류완료":"#6366f1","담당자배정":"#3b82f6",
                     "현장처리중":"#f59e0b","완료":"#10b981","분쟁종결":"#059669"}
        fig4 = px.bar(sc, x="상태", y="건수", color="상태",
                      color_discrete_map=color_map, height=270, text="건수")
        fig4.update_layout(margin=dict(t=10,b=10), showlegend=False)
        fig4.update_traces(textposition="outside")
        st.plotly_chart(fig4, use_container_width=True)
    with c5:
        st.markdown('<div class="sh">⚡ RPA 자동화율 현황</div>', unsafe_allow_html=True)
        rpa_items = [
            ("관리비 고지서 발행", 80),
            ("계약 만료 알림", 100),
            ("민원 접수·분류", 70),
            ("점검 일정 생성", 90),
            ("담당자 자동배정", 75),
        ]
        rpa_html = ""
        for label, pct in rpa_items:
            color = "#10b981" if pct >= 90 else "#2563eb" if pct >= 70 else "#f59e0b"
            rpa_html += f"""
            <div class="rpa-row">
              <div class="rpa-label">{label}</div>
              <div class="rpa-bar-bg">
                <div class="rpa-bar-fill" style="width:{pct}%;background:{color};">{pct}%</div>
              </div>
            </div>"""
        st.markdown(rpa_html, unsafe_allow_html=True)

    # ── KPI 목표 대비 달성률 ──
    st.markdown('<div class="sh">🎯 핵심 성과 목표 (KPI) 달성 현황</div>', unsafe_allow_html=True)
    kpi_table = pd.DataFrame({
        "지표": ["민원처리 시간 단축", "점검업무 시간 단축", "사후보수비용 절감", "입주민 만족도 향상", "실증데이터 확보"],
        "목표": ["67% 개선 (3일→1일)", "50% 단축", "20% 절감", "20% 향상", "10,000건"],
        "현재달성": ["67.4%", "48.2%", "14.3%", "12.1%", "3,847건"],
        "달성률(%)": [100, 96, 72, 61, 38],
        "상태": ["✅ 달성", "🔶 근접", "🔶 진행중", "🔶 진행중", "🔶 진행중"],
    })
    st.dataframe(kpi_table, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════
# PAGE 2: 비전 AI · 드론 정밀 진단
# ══════════════════════════════════════════════════════
elif page == "✈ 비전AI · 드론 정밀진단":
    st.title("✈ 멀티모달 드론 & 비전AI 정밀진단")
    st.caption("Y-MaskNet / Mask R-CNN 인스턴스 세그멘테이션 | 균열·누수·드라이비트 화재취약 탐지")

    tab1, tab2, tab3 = st.tabs(["🖼 AI 이미지 분석", "📊 탐지 결과 현황", "🗺 세움터·FMS 연동 현황"])

    with tab1:
        st.markdown("##### 이미지 업로드 또는 샘플 선택 후 AI 분석 실행")
        col_l, col_r = st.columns([1, 1])
        with col_l:
            upload_type = st.radio("입력 방식", ["📱 앱 업로드 (입주민)", "✈ 드론 스캔 (HSIA)"],
                                   horizontal=True,
                                   help="이미지를 어떤 방식으로 입력할지 선택하세요 📷\n\n"
                                        "• 앱 업로드: 입주민이 스마트폰으로 촬영한 사진\n"
                                        "• 드론 스캔: HSIA 드론이 외벽을 정밀 촬영한 사진")
            uploaded = st.file_uploader("이미지 업로드", type=["jpg","jpeg","png"],
                                        help="분석할 건물 외벽·내부 사진을 올려주세요 🖼️\n"
                                             "지원 형식: JPG, JPEG, PNG (최대 50MB)\n"
                                             "사진이 없으면 아래 샘플 시나리오를 선택하세요.")

            st.divider()
            sample = st.selectbox("또는 샘플 시나리오 선택", [
                "① 수직균열 0.35mm — 외벽 3층 (고위험)",
                "② 누수흔적 — 지하 1층 천장 (중위험)",
                "③ 드라이비트 화재취약 — 외벽 전면 (고위험)",
                "④ 옥상 박리손상 2.1mm (고위험)",
                "⑤ 수평균열 0.08mm — 계단실 (저위험)",
            ], help="실제 사진이 없을 때 미리 준비된 예시를 선택하세요 📋\n\n"
                    "• 🔴 고위험: 즉시 전문가 점검 필요\n"
                    "• 🟡 중위험: 30일 내 보수 권고\n"
                    "• 🟢 저위험: 정기점검 유지")
            run_btn = st.button("🤖 Y-MaskNet 분석 실행", type="primary", use_container_width=True,
                                help="버튼을 클릭하면 AI(Y-MaskNet)가 이미지를 분석합니다 🤖\n\n"
                                     "균열 폭(mm), 누수, 드라이비트 화재취약 구간을\n"
                                     "자동으로 탐지하고 위험도를 판정합니다.\n"
                                     "분석 소요 시간: 약 2초")

        with col_r:
            if run_btn:
                with st.spinner("Y-MaskNet (Mask R-CNN) 추론 중..."):
                    time.sleep(1.8)

                # 시나리오별 결과
                scenarios = {
                    "①": {"유형":"수직균열","폭":0.35,"위험":"고","신뢰":0.94,
                           "기준":"0.2mm 초과","색":"#dc2626","조치":"구조전문가 즉시 현장 점검",
                           "draw":"crack_v"},
                    "②": {"유형":"누수흔적","폭":0.12,"위험":"중","신뢰":0.88,
                           "기준":"습윤면적 200cm²","색":"#3b82f6","조치":"30일내 방수 보수",
                           "draw":"leak"},
                    "③": {"유형":"드라이비트 화재취약","폭":0.0,"위험":"고","신뢰":0.91,
                           "기준":"KFS 화재안전기준","색":"#f97316","조치":"즉시 난연재 교체 또는 방화도료 처리",
                           "draw":"dryvit"},
                    "④": {"유형":"옥상 박리손상","폭":2.10,"위험":"고","신뢰":0.89,
                           "기준":"0.5mm 초과","색":"#9333ea","조치":"우레탄 방수 긴급 시공",
                           "draw":"peel"},
                    "⑤": {"유형":"수평균열","폭":0.08,"위험":"저","신뢰":0.79,
                           "기준":"0.2mm 미만","색":"#16a34a","조치":"정기점검 주기 유지",
                           "draw":"crack_h"},
                }
                key = sample[0]
                sc = scenarios[key]

                # 가상 이미지 생성
                img = Image.new("RGB", (500, 360), (195, 188, 178))
                draw = ImageDraw.Draw(img)
                # 벽면 텍스처
                for x in range(0, 500, 50):
                    draw.line([(x,0),(x,360)], fill=(175,168,158), width=1)
                for y in range(0, 360, 35):
                    draw.line([(0,y),(500,y)], fill=(175,168,158), width=1)

                if sc["draw"] == "crack_v":
                    pts = [(210,50),(215,150),(205,250),(220,340)]
                    for i in range(len(pts)-1):
                        draw.line([pts[i], pts[i+1]], fill=(40,30,20), width=4)
                    draw.rectangle([185,40,245,350], outline="#dc2626", width=3)
                    draw.text((187,25), f"수직균열 {sc['폭']}mm [{int(sc['신뢰']*100)}%]", fill="#dc2626")
                elif sc["draw"] == "leak":
                    draw.ellipse([100,90,350,260], fill=(130,155,175,200), outline="#3b82f6", width=3)
                    draw.text((102,75), f"누수흔적 [{int(sc['신뢰']*100)}%]", fill="#3b82f6")
                elif sc["draw"] == "dryvit":
                    for y in range(0,360,30):
                        draw.rectangle([0,y,500,y+28], fill=(210,190,160), outline=(180,160,130))
                    draw.rectangle([10,10,490,350], outline="#f97316", width=4)
                    draw.text((12,355), f"드라이비트 화재취약 [{int(sc['신뢰']*100)}%]", fill="#f97316")
                elif sc["draw"] == "peel":
                    for i in range(8):
                        x,y = random.randint(50,450), random.randint(50,310)
                        r = random.randint(15,45)
                        draw.ellipse([x-r,y-r,x+r,y+r], fill=(155,145,135), outline="#9333ea", width=2)
                    draw.rectangle([30,30,470,330], outline="#9333ea", width=3)
                    draw.text((32,15), f"박리손상 {sc['폭']}mm [{int(sc['신뢰']*100)}%]", fill="#9333ea")
                else:
                    draw.line([(80,180),(420,185)], fill=(40,30,20), width=3)
                    draw.rectangle([70,165,430,200], outline="#16a34a", width=3)
                    draw.text((72,150), f"수평균열 {sc['폭']}mm [{int(sc['신뢰']*100)}%]", fill="#16a34a")

                buf = io.BytesIO()
                img.save(buf, "PNG")
                st.image(buf.getvalue(), caption="AI 세그멘테이션 오버레이 결과", use_container_width=True)

                # 결과 메트릭
                r1,r2,r3,r4 = st.columns(4)
                r1.metric("탐지 유형", sc["유형"],
                          help="AI가 이미지에서 탐지한 손상의 종류입니다 🔍\n"
                               "균열·누수·드라이비트·박리 4가지 유형을 자동 구분합니다.")
                r2.metric("AI 신뢰도", f"{int(sc['신뢰']*100)}%",
                          help="AI 탐지 결과에 대한 신뢰도(확신도)입니다 🎯\n"
                               "• 90%↑: 매우 신뢰할 수 있는 결과\n"
                               "• 70~90%: 신뢰 가능, 현장 확인 권장\n"
                               "• 70%↓: 재촬영 또는 전문가 확인 필요")
                r3.metric("위험도", f"{'🔴' if sc['위험']=='고' else '🟡' if sc['위험']=='중' else '🟢'} {sc['위험']}",
                          help="AI가 탐지 결과를 기반으로 판정한 위험도입니다 🚦\n\n"
                               "• 🔴 고: 기준치 초과, 즉시 전문가 점검 필요\n"
                               "• 🟡 중: 30일 내 보수 권고\n"
                               "• 🟢 저: 정기점검 수준, 모니터링 유지")
                r4.metric("손상폭", f"{sc['폭']} mm" if sc['폭'] > 0 else "면적 분석",
                          help="균열의 경우 폭(mm)을 정량 측정합니다 📏\n"
                               "기준: 0.2mm 초과 시 고위험 판정\n"
                               "누수·드라이비트는 면적(cm²)으로 분석합니다.")

                # 위험도별 알림
                if sc["위험"] == "고":
                    st.error(f"🚨 **고위험** | 판정기준: {sc['기준']} | 권장조치: **{sc['조치']}**")
                elif sc["위험"] == "중":
                    st.warning(f"⚡ **중위험** | 판정기준: {sc['기준']} | 권장조치: **{sc['조치']}**")
                else:
                    st.success(f"✅ **저위험** | 판정기준: {sc['기준']} | 권장조치: **{sc['조치']}**")

                # 자동 작업지시서
                with st.expander("📋 자동 생성 작업지시서 (Work Order)"):
                    wo = pd.DataFrame({
                        "항목": ["단지","탐지방법","손상유형","위험도","판정기준","권장조치","조치기한","담당팀","AI모델","분석일시"],
                        "내용": [selected_cpx[:25], upload_type, sc["유형"], sc["위험"],
                                 sc["기준"], sc["조치"],
                                 "즉시" if sc["위험"]=="고" else "30일 이내" if sc["위험"]=="중" else "정기점검",
                                 "시설관리 1팀", "Y-MaskNet v2.1 (세종대학교 개발)",
                                 datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                    })
                    st.table(wo)

            else:
                st.info("👈 좌측에서 시나리오를 선택하고 **Y-MaskNet 분석 실행** 버튼을 클릭하세요.")
                st.markdown("""
                **지원 탐지 항목:**
                - 🔴 수직·수평 균열 (폭 0.2mm ~ 2.0mm 정량 측정)
                - 🔵 누수흔적·습윤면적
                - 🟠 드라이비트(가연성 외벽재) 화재취약 구조
                - 🟣 박리·박락·표면손상

                **탐지 기준:** KICT 시설물 유지관리 가이드라인 + KFS 한국화재안전기준
                """)

    with tab2:
        st.markdown('<div class="sh">📋 전체 AI 탐지 결과 목록</div>', unsafe_allow_html=True)
        risk_f = st.multiselect("위험도 필터", ["고","중","저"], default=["고","중","저"], key="dmg_risk",
                               help="표시할 위험도 등급을 선택하세요 🔍\n\n"
                                    "• 🔴 고: 즉시 조치 필요 (균열 0.2mm↑ 등)\n"
                                    "• 🟡 중: 30일 내 보수 권고\n"
                                    "• 🟢 저: 정기점검 수준, 당장 위험 없음")
        disp = damage_df[damage_df["위험도"].isin(risk_f)].copy()
        icon = {"고":"🔴","중":"🟡","저":"🟢"}
        disp["위험도"] = disp["위험도"].map(lambda r: f"{icon.get(r,'')} {r}")
        st.dataframe(disp, use_container_width=True, hide_index=True, height=280)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**손상 유형별 건수**")
            vc = damage_df["유형"].value_counts().reset_index()
            vc.columns = ["유형","건수"]
            fig = px.bar(vc, x="건수", y="유형", orientation="h", height=220,
                         color="건수", color_continuous_scale="Reds")
            fig.update_layout(margin=dict(t=5,b=5), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            st.markdown("**위험도 × 탐지방법 분포**")
            ct = damage_df.groupby(["탐지방법","위험도"]).size().reset_index(name="건수")
            fig2 = px.bar(ct, x="탐지방법", y="건수", color="위험도",
                          color_discrete_map={"고":"#dc2626","중":"#d97706","저":"#16a34a"},
                          height=220, barmode="group")
            fig2.update_layout(margin=dict(t=5,b=5))
            st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.markdown('<div class="sh">🗺 세움터(건축물 도면) × FMS(시설물정보) 연동 현황</div>', unsafe_allow_html=True)
        st.dataframe(facility_df[["단지","준공년도","경과년수","세대수","외벽재질",
                                   "방수공법","노후도점수","FMS연동","세움터연동","마지막드론점검"]],
                     use_container_width=True, hide_index=True)
        st.markdown("""
        > **디지털 트윈 구축 현황:** 세움터(도면) + FMS(시설물정보) + 드론 스캔 데이터를
        > 융합하여 건물별 3D 노후도 모델을 자동 생성합니다.
        > 연동 완료 단지는 건물 전체 수명주기 예측이 가능합니다.
        """)

        # 노후도 게이지
        age_fig = go.Figure()
        for _, row in facility_df.iterrows():
            age_fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=row["노후도점수"],
                title={"text": row["단지"][:10], "font": {"size": 9}},
                gauge={"axis": {"range": [0,100]},
                       "bar": {"color": "#2563eb" if row["노후도점수"] > 60 else "#dc2626"},
                       "steps": [{"range":[0,40],"color":"#fee2e2"},
                                  {"range":[40,70],"color":"#fef3c7"},
                                  {"range":[70,100],"color":"#d1fae5"}]},
                domain={}
            ))
        # 단순 바 차트로 대체 (게이지 다중은 복잡)
        fig_age = px.bar(facility_df, x="단지", y="노후도점수",
                         color="노후도점수", color_continuous_scale="RdYlGn",
                         height=300, text="노후도점수")
        fig_age.update_layout(margin=dict(t=10,b=10), coloraxis_showscale=True,
                               xaxis_tickangle=-30)
        fig_age.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        st.plotly_chart(fig_age, use_container_width=True)

# ══════════════════════════════════════════════════════
# PAGE 3: RPA 행정 자동화
# ══════════════════════════════════════════════════════
elif page == "🤖 RPA 행정 자동화":
    st.title("🤖 지능형 행정 자동화 (RPA + AI)")
    st.caption("관리비 자동발행 80% · 계약알림 100% · 민원분류 70% · 점검일정 90%")

    tab1, tab2, tab3, tab4 = st.tabs(["📄 관리비 고지서", "📅 계약 만료 알림", "🗓 점검 일정 자동생성", "📊 자동화 성과"])

    with tab1:
        st.markdown('<div class="sh">📄 관리비 고지서 자동 발행 현황 (RPA 80% 자동화)</div>', unsafe_allow_html=True)

        b1, b2, b3, b4 = st.columns(4)
        b1.metric("총 발행 세대", f"{len(billing_df):,}세대",
                  help="이번 달 관리비 고지서 발행 대상 전체 세대 수입니다 🏠")
        b2.metric("자동발행 완료", f"{(billing_df['발행상태']=='자동발행완료').sum():,}건",
                  help="RPA가 사람 개입 없이 자동으로 발행 완료한 건수입니다 🤖\n"
                       "전체의 80%를 자동화하여 담당자 업무를 대폭 줄였습니다.")
        b3.metric("오류 확인필요", f"{(billing_df['발행상태']=='오류확인필요').sum()}건", delta="수동처리 필요", delta_color="inverse",
                  help="자동 발행 중 오류가 발생해 담당자가 직접 확인해야 하는 건수입니다 ⚠️\n"
                       "오류 원인은 주로 세대 정보 불일치입니다.")
        b4.metric("자동화율", "80.0%", delta="목표 달성", delta_color="normal",
                  help="전체 고지서 발행 업무 중 RPA가 자동 처리한 비율입니다 📈\n"
                       "목표: 80% 이상 — 현재 달성 완료")

        st.markdown("**📋 고지서 발행 샘플 (상위 30건)**")
        st.dataframe(billing_df.head(30)[["단지","호수","관리비_만원","전기료_만원","수도료_만원","청구월","발행상태","발행일시"]],
                     use_container_width=True, hide_index=True, height=280)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**발행 상태 분포**")
            vc2 = billing_df["발행상태"].value_counts()
            fig = px.pie(values=vc2.values, names=vc2.index, height=220, hole=0.4,
                         color_discrete_map={"자동발행완료":"#10b981","오류확인필요":"#ef4444"})
            fig.update_layout(margin=dict(t=5,b=5))
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            st.markdown("**단지별 평균 관리비 (만원)**")
            avg_bill = billing_df.groupby("단지")["관리비_만원"].mean().reset_index()
            avg_bill["단지"] = avg_bill["단지"].str[:10]
            fig2 = px.bar(avg_bill, x="관리비_만원", y="단지", orientation="h", height=220,
                          color="관리비_만원", color_continuous_scale="Blues")
            fig2.update_layout(margin=dict(t=5,b=5), coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.markdown('<div class="sh">📅 계약 만료 알림 자동 발송 (RPA 100% 자동화)</div>', unsafe_allow_html=True)
        today = date.today()
        soon = contract_df[contract_df["잔여일수"] <= 60].sort_values("잔여일수")
        urgent = contract_df[contract_df["잔여일수"] < 0]
        normal = contract_df[contract_df["잔여일수"] > 60]

        cc1, cc2, cc3 = st.columns(3)
        cc1.metric("전체 계약", f"{len(contract_df)}건",
                   help="현재 관리 중인 전체 임대 계약 건수입니다 📄")
        cc2.metric("60일내 만료", f"{len(soon)}건", delta="알림발송 완료", delta_color="normal",
                   help="앞으로 60일 안에 계약이 끝나는 세대입니다 ⏳\n"
                        "RPA가 입주민에게 자동으로 갱신 안내 문자를 보냈습니다.")
        cc3.metric("이미 만료", f"{len(urgent)}건", delta="갱신협의 진행중", delta_color="inverse",
                   help="계약 만료일이 이미 지난 세대입니다 🔴\n"
                        "담당자가 갱신 협의를 진행 중입니다.")

        st.markdown("**⚠️ 60일 이내 만료 예정 계약**")
        disp_c = soon.copy()
        disp_c["D-Day"] = disp_c["잔여일수"].apply(lambda d: f"D{d:+d}" if d >= 0 else f"만료 {abs(d)}일 경과")
        st.dataframe(disp_c[["입주민번호","단지","호수","계약만료일","D-Day","알림상태","자동알림","갱신의향"]],
                     use_container_width=True, hide_index=True, height=280)

        # 갱신의향 파이
        gi = contract_df["갱신의향"].value_counts()
        fig3 = px.pie(values=gi.values, names=gi.index, height=200, hole=0.3,
                      color_discrete_sequence=["#10b981","#f59e0b","#ef4444"],
                      title="갱신 의향 분포")
        fig3.update_layout(margin=dict(t=30,b=5))
        st.plotly_chart(fig3, use_container_width=True)

    with tab3:
        st.markdown('<div class="sh">🗓 AI 기반 점검 일정 자동 생성 (RPA 90% 자동화)</div>', unsafe_allow_html=True)
        st.info("노후도 점수, 마지막 점검일, 탐지 이력을 종합하여 AI가 최적 점검 일정을 자동 생성합니다.")

        gen_schedule = st.button("🤖 AI 점검 일정 자동 생성", type="primary",
                               help="버튼을 클릭하면 AI가 단지별 점검 일정을 자동으로 만들어줍니다 📅\n\n"
                                    "노후도 점수 + 마지막 점검일 + 손상 탐지 이력을 종합하여\n"
                                    "가장 시급한 단지부터 우선순위를 정해 일정을 생성합니다.")
        if gen_schedule:
            schedule_rows = []
            for _, row in facility_df.iterrows():
                score = row["노후도점수"]
                if score < 50:
                    freq = "월 1회"
                    next_insp = date.today() + timedelta(days=random.randint(1,15))
                    priority = "긴급"
                elif score < 70:
                    freq = "분기 1회"
                    next_insp = date.today() + timedelta(days=random.randint(15,45))
                    priority = "일반"
                else:
                    freq = "반기 1회"
                    next_insp = date.today() + timedelta(days=random.randint(45,90))
                    priority = "예정"
                schedule_rows.append({
                    "단지": row["단지"][:15],
                    "노후도점수": round(score,1),
                    "점검주기": freq,
                    "다음점검일": next_insp.strftime("%Y-%m-%d"),
                    "우선순위": priority,
                    "점검방법": "드론+앱" if score < 60 else "앱",
                    "담당": random.choice(["HSIA 드론팀", "시설1팀", "시설2팀"]),
                })
            sdf = pd.DataFrame(schedule_rows)
            st.success("✅ 점검 일정 자동 생성 완료! (AI 우선순위 배정 완료)")
            st.dataframe(sdf, use_container_width=True, hide_index=True)
        else:
            st.markdown("버튼을 클릭하면 **AI가 단지별 노후도 × 점검이력 × 손상탐지 결과**를 분석하여 최적 일정을 생성합니다.")

    with tab4:
        st.markdown('<div class="sh">📊 RPA 자동화 성과 (기존 대비 개선)</div>', unsafe_allow_html=True)
        before_after = pd.DataFrame({
            "업무": ["관리비 고지서 발행","계약 만료 알림","민원 접수·분류","점검 일정 수립","담당자 배정","점검결과 보고"],
            "기존(수동)_시간": ["4시간/월","3시간/월","30분/건","2시간/회","20분/건","3시간/건"],
            "RPA자동화_시간": ["48분/월(80%↓)","0분(100%↓)","9분/건(70%↓)","12분/회(90%↓)","5분/건(75%↓)","자동생성(90%↓)"],
            "자동화율": [80,100,70,90,75,90],
            "연간절감_만원": [240,120,360,180,150,300],
        })
        st.dataframe(before_after, use_container_width=True, hide_index=True)

        fig_rpa = px.bar(before_after, x="업무", y="자동화율",
                         color="자동화율", color_continuous_scale="Greens",
                         height=300, text="자동화율",
                         labels={"자동화율": "RPA 자동화율 (%)"},
                         title="업무별 RPA 자동화율")
        fig_rpa.add_hline(y=80, line_dash="dash", line_color="#dc2626", annotation_text="목표 80%")
        fig_rpa.update_traces(texttemplate="%{text}%", textposition="outside")
        fig_rpa.update_layout(margin=dict(t=40,b=10))
        st.plotly_chart(fig_rpa, use_container_width=True)

        total_save = before_after["연간절감_만원"].sum()
        st.success(f"💰 **RPA 자동화를 통한 연간 절감 추정액: {total_save:,}만원 ({total_save/100:.1f}억원)**  ← 목표: 연간 1억원 절감")

# ══════════════════════════════════════════════════════
# PAGE 4: AI 민원 관리
# ══════════════════════════════════════════════════════
elif page == "📋 AI 민원 관리":
    st.title("📋 AI 민원 처리 워크플로우")
    st.caption("RPA 70% 자동분류 · AI 우선순위 배정 · 담당자 자동지정 · 예방 조치 자동 연계")

    tab1, tab2, tab3 = st.tabs(["📋 민원 목록 & 관리", "📱 입주민 앱 민원 접수", "📊 처리 통계"])

    with tab1:
        # 필터
        f1,f2,f3,f4 = st.columns(4)
        with f1: f_type = st.multiselect("유형", list(COMPLAINT_TYPES.keys()),
                                          default=list(COMPLAINT_TYPES.keys()), key="c1",
                                          help="보고 싶은 민원 유형만 선택하세요 📋\n"
                                               "체크 해제하면 해당 유형은 목록에서 숨겨집니다.")
        with f2: f_risk = st.multiselect("위험도", ["고","중","저"],
                                          default=["고","중","저"], key="c2",
                                          help="민원 위험도로 필터링합니다 🚦\n\n"
                                               "• 고: 구조 안전 관련, 즉시 대응\n"
                                               "• 중: 3일 내 처리\n"
                                               "• 저: 7일 내 처리")
        with f3: f_stat = st.multiselect("상태", complaint_df["상태"].unique().tolist(),
                                          default=complaint_df["상태"].unique().tolist(), key="c3",
                                          help="민원 처리 단계로 필터링합니다 🔄\n\n"
                                               "접수 → AI분류완료 → 담당자배정 → 현장처리중 → 완료")
        with f4: f_site = st.multiselect("수요처", ["SH공사","경북개발공사"],
                                          default=["SH공사","경북개발공사"], key="c4",
                                          help="어느 기관 단지의 민원을 볼지 선택하세요 🏢\n"
                                               "둘 다 선택하면 전체 민원이 표시됩니다.")

        fc = complaint_df[
            complaint_df["유형"].isin(f_type) &
            complaint_df["위험도"].isin(f_risk) &
            complaint_df["상태"].isin(f_stat) &
            complaint_df["수요처"].isin(f_site)
        ].copy()

        icon = {"고":"🔴","중":"🟡","저":"🟢"}
        fc["위험도"] = fc["위험도"].map(lambda r: f"{icon.get(r,'')} {r}")
        st.dataframe(fc[["민원번호","수요처","유형","위험도","접수일","상태","처리일수","AI분류","AI신뢰도","담당자"]],
                     use_container_width=True, hide_index=True, height=380)

        # AI 처리 흐름
        st.markdown('<div class="sh">🔄 AI 민원 처리 워크플로우</div>', unsafe_allow_html=True)
        steps = [
            ("1️⃣ 민원 접수", "입주민 앱 사진+텍스트 업로드\n또는 웹/전화 접수"),
            ("2️⃣ AI 자동 분류 (RPA 70%)", "유형·위험도 자동 분류\nAI 신뢰도 72~97%"),
            ("3️⃣ 담당자 자동 배정 (75%)", "위험도·단지·업무량 기반\n최적 담당자 자동 지정"),
            ("4️⃣ 현장 조치", "드론/앱 재점검\n실측·보수 시행"),
            ("5️⃣ 예방 정비 연계", "AI 사전 예방 정비 엔진\n위험도 재평가·재발 방지"),
            ("6️⃣ 처리 완료", "결과 보고서 발급\n입주민 앱 자동 통보"),
        ]
        cols = st.columns(6)
        for col, (title, desc) in zip(cols, steps):
            with col:
                st.markdown(f"""
                <div class="step-card">
                    <div class="step-title">{title}</div>
                    <div class="step-desc">{desc}</div>
                </div>""", unsafe_allow_html=True)

    with tab2:
        st.markdown("#### 📱 입주민 앱 — 비대면 민원 접수 시뮬레이션")
        st.caption("세대 내부(화구, 수전 등) 접근 어려운 공간을 입주민이 직접 촬영·업로드")

        with st.form("new_complaint"):
            r1,r2 = st.columns(2)
            with r1:
                nc_site = st.selectbox("수요처", ["SH공사","경북개발공사"],
                                       help="민원을 접수할 기관을 선택하세요 🏢\n"
                                            "• SH공사: 서울 소재 단지\n"
                                            "• 경북개발공사: 경북 소재 단지")
                nc_cpx = st.selectbox("단지", ALL_COMPLEXES,
                                      help="문제가 발생한 단지를 선택하세요 🏘️\n"
                                           "단지명과 준공연도가 함께 표시됩니다.")
                nc_unit = st.text_input("호수", placeholder="예: 101동 302호",
                                        help="어느 동·호수에서 발생한 문제인지 입력하세요 🚪\n"
                                             "예) 101동 302호, 지하 1층 공용부 등")
                nc_type = st.selectbox("손상 유형", list(COMPLAINT_TYPES.keys()),
                                       help="발생한 문제의 종류를 선택하세요 🔧\n"
                                            "AI가 선택한 유형을 기반으로 위험도를 자동 분류합니다.")
            with r2:
                nc_loc = st.text_input("손상 위치", placeholder="예: 화장실 천장, 주방 수전 하단",
                                       help="건물 내 어느 위치에 문제가 있는지 구체적으로 입력하세요 📍\n"
                                            "예) 화장실 천장, 주방 수전 하단, 거실 벽면 등")
                nc_desc = st.text_area("상세 설명", placeholder="언제부터 생겼는지, 어느 정도 심한지 등", height=90,
                                       help="문제 상황을 자세히 설명해주세요 📝\n\n"
                                            "• 언제부터 시작됐나요?\n"
                                            "• 얼마나 심각한가요? (범위, 냄새, 소리 등)\n"
                                            "• 이전에 같은 문제가 있었나요?\n"
                                            "자세할수록 AI가 더 정확하게 분류합니다.")
                nc_photo = st.file_uploader("사진 첨부", type=["jpg","jpeg","png"],
                                            help="문제가 있는 부분을 찍은 사진을 첨부하세요 📸\n"
                                                 "사진이 있으면 AI 분류 정확도가 높아집니다.\n"
                                                 "지원 형식: JPG, JPEG, PNG (최대 50MB)")
            submit_c = st.form_submit_button("📤 민원 접수하기", type="primary", use_container_width=True,
                                             help="클릭하면 민원이 즉시 접수되고 AI가 자동 분류합니다 ✅\n"
                                                  "위험도에 따라 담당자에게 자동으로 알림이 발송됩니다.")

        if submit_c:
            with st.spinner("AI 분류 엔진 분석 중..."):
                time.sleep(1.3)
            info = COMPLAINT_TYPES[nc_type]
            new_num = f"CM-2026-{random.randint(2000,9999)}"
            ai_score = round(random.uniform(0.78, 0.97), 2)
            st.success(f"✅ 민원 접수 완료 — **{new_num}**")
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("민원번호", new_num,
                      help="AI가 자동 부여한 민원 고유 번호입니다 🔢\n이 번호로 처리 현황을 추적할 수 있습니다.")
            m2.metric("AI 위험도 판정", f"{'🔴' if info['위험도']=='고' else '🟡' if info['위험도']=='중' else '🟢'} {info['위험도']}",
                      help="AI가 손상 유형을 분석해 판정한 위험도입니다 🚦\n\n"
                           "• 🔴 고: 구조 안전 위험, 즉시 대응\n"
                           "• 🟡 중: 3일 내 현장 점검\n"
                           "• 🟢 저: 7일 내 정기 처리")
            m3.metric("AI 신뢰도", f"{int(ai_score*100)}%",
                      help="AI 자동 분류 결과에 대한 신뢰도입니다 🎯\n"
                           "90%↑: 매우 신뢰 / 70~90%: 담당자 확인 권장 / 70%↓: 수동 분류")
            m4.metric("RPA 자동화율", f"{info['rpa자동화']}%",
                      help="이 유형의 민원 처리에서 RPA가 자동으로 처리하는 비율입니다 🤖\n"
                           "높을수록 담당자 개입 없이 자동으로 처리됩니다.")
            if info["위험도"] == "고":
                st.error("🚨 **고위험 민원** — 담당팀장에게 즉시 문자 발송 및 긴급 작업지시서 생성 완료")
            elif info["위험도"] == "중":
                st.warning("⚡ **중위험 민원** — 담당자 배정 완료. 3일 내 현장 점검 예약")
            else:
                st.info("📬 **저위험 민원** — 정기점검 큐 등록. 7일 내 처리 예정")

    with tab3:
        col_a,col_b = st.columns(2)
        with col_a:
            st.markdown("**월별 민원 접수 · 완료 추이**")
            months = [(datetime.now()-timedelta(days=30*i)).strftime("%Y-%m") for i in range(5,-1,-1)]
            fig = go.Figure()
            fig.add_bar(x=months, y=[random.randint(10,22) for _ in months], name="접수", marker_color="#3b82f6")
            fig.add_bar(x=months, y=[random.randint(8,20)  for _ in months], name="완료", marker_color="#10b981")
            fig.update_layout(barmode="group", height=280, margin=dict(t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            st.markdown("**처리 기간 분포 (완료 민원)**")
            done_days = complaint_df[complaint_df["상태"]=="완료"]["처리일수"].dropna()
            fig2 = px.histogram(done_days, nbins=20, height=280,
                                labels={"value":"처리 기간 (일)","count":"건수"},
                                color_discrete_sequence=["#6366f1"])
            fig2.add_vline(x=1, line_dash="dash", line_color="#dc2626", annotation_text="목표 1일")
            fig2.update_layout(margin=dict(t=10,b=10))
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("**AI 분류 vs 수동 처리 비율**")
        ac = complaint_df["AI분류"].value_counts()
        fig3 = px.pie(values=ac.values, names=ac.index, height=200, hole=0.4,
                      color_discrete_map={"자동":"#10b981","수동":"#f59e0b"})
        fig3.update_layout(margin=dict(t=5,b=5))
        st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════
# PAGE 5: IoT · 디지털 트윈
# ══════════════════════════════════════════════════════
elif page == "📡 IoT · 디지털 트윈":
    st.title("📡 IoT 실시간 센서 모니터링")
    st.caption("온도·습도·전력·진동·CO 농도 | 임계값 초과 시 자동알림 | SH FMS 연동")

    latest = iot_df.iloc[-1]
    c1,c2,c3,c4,c5 = st.columns(5)

    SENSOR_HELP = {
        "온도":   "실내 온도를 측정합니다 🌡️\n기준(30°C) 초과 시 환기 권고 문자를 자동 발송합니다.",
        "습도":   "실내 습도를 측정합니다 💧\n기준(70%) 초과 시 누수 가능성 — 3일 내 점검을 예약합니다.",
        "전력":   "세대별 시간당 전력 소비량(kWh)입니다 ⚡\n기준(4.0 kWh) 초과 시 전기 안전 점검을 자동 예약합니다.",
        "진동":   "건물 구조 진동 가속도(g)를 측정합니다 📳\n기준(0.5 g) 초과 시 구조팀에 긴급 점검을 요청합니다.",
        "CO농도": "일산화탄소(CO) 농도(ppm)를 측정합니다 🌫️\n기준(10 ppm) 초과 시 환기팀 즉시 출동 + 담당자 문자 발송",
    }

    def sensor_kpi(col, name, val, unit, thr, higher_bad=True):
        over = (val > thr) if higher_bad else (val < thr)
        badge = "🔴 경고" if over else "🟢 정상"
        with col:
            st.metric(f"{name} {badge}", f"{val:.1f}{unit}", delta=f"기준 {thr}{unit}",
                      delta_color="inverse" if over else "off",
                      help=SENSOR_HELP.get(name, ""))

    sensor_kpi(c1, "온도",   latest["온도"],   "°C",  30)
    sensor_kpi(c2, "습도",   latest["습도"],   "%",   70)
    sensor_kpi(c3, "전력",   latest["전력_kWh"],"kWh", 4.0)
    sensor_kpi(c4, "진동",   latest["진동_g"], "g",   0.5)
    sensor_kpi(c5, "CO농도", latest["CO_ppm"], "ppm", 10)

    st.divider()
    period = st.slider("조회 기간 (일)", 1, 30, 7,
                       help="IoT 센서 그래프에서 볼 기간을 조절하세요 📅\n\n"
                            "• 1일: 오늘 하루 데이터만\n"
                            "• 7일: 최근 1주일 (기본값)\n"
                            "• 30일: 최근 한 달 전체\n"
                            "슬라이더를 오른쪽으로 끌수록 더 긴 기간을 봅니다.")
    cut = datetime.now() - timedelta(days=period)
    vdf = iot_df[iot_df["ts"] >= cut]

    fig = make_subplots(rows=2, cols=3,
                        subplot_titles=["온도 (°C)","습도 (%)","전력 (kWh)","진동 (g)","CO 농도 (ppm)",""])
    palette = ["#ef4444","#3b82f6","#f59e0b","#8b5cf6","#06b6d4"]
    thresholds = [30, 70, 4.0, 0.5, 10]
    cols_data = ["온도","습도","전력_kWh","진동_g","CO_ppm"]
    positions = [(1,1),(1,2),(1,3),(2,1),(2,2)]
    for (row,col), dcol, thr, clr in zip(positions, cols_data, thresholds, palette):
        fig.add_trace(go.Scatter(x=vdf["ts"], y=vdf[dcol], line=dict(color=clr, width=1.5),
                                 name=dcol, showlegend=False), row=row, col=col)
        fig.add_hline(y=thr, line_dash="dash", line_color="#94a3b8", row=row, col=col)
    fig.update_layout(height=430, margin=dict(t=40,b=10))
    st.plotly_chart(fig, use_container_width=True)

    # 이상 이벤트 로그
    st.markdown('<div class="sh">🚨 이상 감지 이벤트 로그 (자동 기록)</div>', unsafe_allow_html=True)
    events = [
        {"시각":"2026-04-07 02:14","센서":"CO 농도","측정값":"16.2 ppm","기준":"10 ppm","단지":"마포B동","자동조치":"담당자 문자 + 환기팀 출동 요청"},
        {"시각":"2026-04-06 18:33","센서":"진동","측정값":"0.85 g","기준":"0.5 g","단지":"강남A동","자동조치":"구조팀 긴급 점검 요청"},
        {"시각":"2026-04-05 14:21","센서":"습도","측정값":"78.4 %","기준":"70 %","단지":"노원C동","자동조치":"누수 모니터링 강화 + 3일 내 점검 예약"},
        {"시각":"2026-04-04 09:05","센서":"온도","측정값":"32.1 °C","기준":"30 °C","단지":"구미A동","자동조치":"환기 권고 문자 발송"},
        {"시각":"2026-04-03 03:44","센서":"전력","측정값":"5.8 kWh","기준":"4.0 kWh","단지":"서초E동","자동조치":"전기안전점검 자동 예약"},
    ]
    st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════
# PAGE 6: AI 사전 예방 정비 엔진
# ══════════════════════════════════════════════════════
elif page == "🛡 AI 사전 예방 정비":
    st.title("🛡 AI 사전 예방 정비 엔진")
    st.caption("손상이 사고로 번지기 전 — XAI 위험도 스코어링 · IoT 이상 감지 · 예방 정비 지시 자동 출력")

    # KPI
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown('<div class="kpi-card-red"><div class="label">고위험 경보 단지</div><div class="value">3</div><div class="sub">즉시 예방 정비 필요</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="kpi-card-amber"><div class="label">중위험 모니터링</div><div class="value">11</div><div class="sub">주간 점검 권고</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="kpi-card-green"><div class="label">예방 조치 완료</div><div class="value">47</div><div class="sub">이번 달 누적</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown('<div class="kpi-card"><div class="label">사고 전환 차단율</div><div class="value">94%</div><div class="sub">AI 조기 경보 효과</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # 단지별 위험도 스코어링
    st.markdown("### 📊 단지별 AI 위험도 스코어 (7개 예방 지표 종합)")

    prevention_data = []
    for cpx in ALL_COMPLEXES[:10]:
        age = 2026 - int(cpx.split("준공: ")[1][:4])
        score = round(
            age * 0.28 +
            random.uniform(10, 30) +   # IoT 이상 누적
            random.uniform(5, 20) +    # 손상 측정값 추이
            random.uniform(5, 15) +    # 점검 이력 경과일
            random.uniform(0, 10),     # 기상 데이터
            1
        )
        score = min(score, 99)
        level = "🔴 고위험" if score >= 70 else ("🟡 중위험" if score >= 40 else "🟢 정상")
        action = "즉시 정비 지시" if score >= 70 else ("주간 점검 권고" if score >= 40 else "정기 모니터링")
        prevention_data.append({
            "단지": cpx[:20],
            "경과년수": f"{age}년",
            "위험도 점수": score,
            "등급": level,
            "권고 조치": action,
        })

    prev_df = pd.DataFrame(prevention_data).sort_values("위험도 점수", ascending=False).reset_index(drop=True)
    st.dataframe(prev_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # XAI SHAP 기여도 — 위험도 판정 근거
    st.markdown("### 🔍 XAI 위험도 판정 근거 (SHAP 기여도)")
    col_l, col_r = st.columns([1, 1])

    with col_l:
        selected_prev = st.selectbox("단지 선택", [r["단지"] for r in prevention_data],
                                    help="XAI 위험도 판정 근거를 볼 단지를 선택하세요 🏘️\n"
                                         "선택하면 아래 막대 그래프가 해당 단지의 AI 판정 이유를 보여줍니다.")
        row = next(r for r in prevention_data if r["단지"] == selected_prev)
        st.metric("위험도 점수", f"{row['위험도 점수']}점", delta=row["등급"],
                  help="AI가 7개 예방 지표를 종합하여 산출한 위험도 점수입니다 🎯\n\n"
                       "• 70점↑: 🔴 고위험 — 즉시 정비 필요\n"
                       "• 40~70점: 🟡 중위험 — 주간 점검 권고\n"
                       "• 40점↓: 🟢 정상 — 정기 모니터링 유지")

    raw_shap = {
        "건물 경과년수 (노후도)": random.uniform(0.20, 0.32),
        "IoT 센서 이상 감지 누적": random.uniform(0.15, 0.25),
        "손상 측정값 추이 (균열폭 진행)": random.uniform(0.12, 0.22),
        "마지막 정기점검 경과일": random.uniform(0.08, 0.16),
        "기상 데이터 (강우·동결 이력)": random.uniform(0.06, 0.14),
        "드라이비트 면적 비율": random.uniform(0.04, 0.10),
        "동일 유형 과거 민원 빈도": random.uniform(0.03, 0.08),
    }
    total_shap = sum(raw_shap.values())
    shap_norm = {k: round(v / total_shap, 3) for k, v in raw_shap.items()}
    shap_sorted = dict(sorted(shap_norm.items(), key=lambda x: x[1], reverse=True))

    fig_prev = px.bar(
        x=list(shap_sorted.values()), y=list(shap_sorted.keys()),
        orientation="h", height=300,
        labels={"x": "기여도 (SHAP value)", "y": ""},
        color=list(shap_sorted.values()), color_continuous_scale="Reds",
        title=f"{selected_prev} — 위험도 판정 근거"
    )
    fig_prev.update_layout(margin=dict(t=40, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig_prev, use_container_width=True)

    st.markdown("---")

    # 예방 정비 지시 자동 출력
    st.markdown("### 📋 예방 정비 지시서 자동 생성")
    with st.form("prevention_form"):
        p1, p2 = st.columns(2)
        with p1:
            prev_cpx = st.selectbox("단지", ALL_COMPLEXES,
                                    help="예방 정비 지시서를 발행할 단지를 선택하세요 🏘️")
            prev_facility = st.selectbox("시설 유형", ["외벽 (드라이비트)", "배관·누수", "전기 설비", "지붕·옥상", "공용 계단·복도"],
                                         help="점검·정비할 시설 종류를 선택하세요 🔧\n\n"
                                              "• 외벽(드라이비트): 화재취약 외장재 점검\n"
                                              "• 배관·누수: 수도관, 천장 누수\n"
                                              "• 전기 설비: 배전반, 전선 노후\n"
                                              "• 지붕·옥상: 방수, 균열\n"
                                              "• 공용 계단·복도: 균열, 낙하물 위험")
        with p2:
            prev_priority = st.selectbox("우선순위", ["🔴 긴급 (48시간 내)", "🟡 우선 (1주 내)", "🟢 일반 (1개월 내)"],
                                         help="AI 위험도 점수에 따라 조치 기한을 정하세요 ⏱️\n\n"
                                              "• 🔴 긴급: 70점↑ 고위험, 48시간 내 착수\n"
                                              "• 🟡 우선: 40~70점 중위험, 1주일 내\n"
                                              "• 🟢 일반: 40점↓ 정상, 1개월 내 처리")
            prev_worker = st.text_input("담당 업체", placeholder="예) ○○유지보수",
                                        help="정비를 담당할 업체 이름을 입력하세요 🏗️\n"
                                             "입력하면 지시서에 자동으로 포함됩니다.\n"
                                             "비워두면 '미지정'으로 표시됩니다.")
        gen_prev = st.form_submit_button("🛡 예방 정비 지시서 생성", type="primary", use_container_width=True,
                                         help="클릭하면 AI가 위험도를 분석하고 정비 지시서를 자동 생성합니다 📋\n"
                                              "생성된 지시서는 TXT 저장, FMS 전송, 담당자 앱 알림으로 발송할 수 있습니다.")

    if gen_prev:
        with st.spinner("AI 위험도 분석 및 정비 지시서 생성 중..."):
            time.sleep(1.5)
        age_p = 2026 - int(prev_cpx.split("준공: ")[1][:4])
        st.success("✅ 예방 정비 지시서가 생성되었습니다.")
        st.markdown(f"""
---
## 🛡 AI 사전 예방 정비 지시서
> **생성일시:** {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}
> **AI 모델:** XAI 위험도 스코어링 엔진 v2.0 (세종대학교 공동 개발)

| 항목 | 내용 |
|------|------|
| 단지 | {prev_cpx[:30]} |
| 건물 경과년수 | {age_p}년 |
| 대상 시설 | {prev_facility} |
| 우선순위 | {prev_priority} |
| 담당 업체 | {prev_worker if prev_worker else '미지정'} |
| AI 위험도 점수 | {round(age_p * 0.28 + random.uniform(20, 50), 1)}점 |

**📌 AI 권고 조치:**
- {prev_facility} 정밀 점검 및 손상 진행 상태 확인
- IoT 센서 이상 징후 재확인 후 임계값 재설정
- 손상 확대 전 선제 보수 시행 → 대형 사고 원천 차단
- 조치 완료 후 드론 재스캔 결과 FMS 업로드
        """)
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            inst_text = f"""AI 사전 예방 정비 지시서
단지: {prev_cpx[:30]}
시설: {prev_facility}
우선순위: {prev_priority}
담당: {prev_worker if prev_worker else '미지정'}
생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
            st.download_button("⬇️ 지시서 저장 (.txt)", data=inst_text.encode("utf-8"),
                               file_name=f"prevention_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                               mime="text/plain", use_container_width=True)
        with col_a2:
            st.button("📤 FMS 자동 전송", use_container_width=True,
                      help="SH공사 / 경북개발공사 FMS 자동 연동")
        with col_a3:
            st.button("📱 담당자 앱 알림", use_container_width=True,
                      help="담당 업체 앱 + 문자 자동 발송")

    # ── KALIS-FMS 데이터 연동 ──────────────────────────────
    st.divider()
    st.markdown('<div class="sh">🛡 Antigravity 엔진 — KALIS-FMS 3중 교차검증</div>', unsafe_allow_html=True)
    st.caption("KALIS-FMS 30년 결함 이력 × 일송건축 설계도면 × 세종대 비선형 FEM → False Positive 0건 목표")

    kalis_col1, kalis_col2 = st.columns([3, 2])
    with kalis_col1:
        import numpy as np
        years = list(range(1, 31))
        degradation_base = [100 - (y ** 1.4) * 0.8 + random.uniform(-2, 2) for y in years]
        degradation_ai   = [100 - (y ** 1.2) * 0.55 + random.uniform(-1, 1) for y in years]
        threshold_line   = [70] * 30

        fig_kalis = go.Figure()
        fig_kalis.add_trace(go.Scatter(x=years, y=degradation_base, name="KALIS 실측 노후도",
                                       line=dict(color="#ef4444", dash="dot"), mode="lines"))
        fig_kalis.add_trace(go.Scatter(x=years, y=degradation_ai, name="Antigravity 예측 곡선",
                                       line=dict(color="#10b981"), mode="lines",
                                       fill="tonexty", fillcolor="rgba(16,185,129,0.08)"))
        fig_kalis.add_trace(go.Scatter(x=years, y=threshold_line, name="정밀안전진단 기준선 (70점)",
                                       line=dict(color="#f59e0b", dash="dash"), mode="lines"))
        fig_kalis.update_layout(height=280, margin=dict(t=10, b=10),
                                xaxis_title="경과 년수", yaxis_title="구조 건전도 지수",
                                legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig_kalis, use_container_width=True)

    with kalis_col2:
        st.markdown("""
        **🔬 3중 교차검증 결과**
        | 검증 레이어 | 데이터 소스 | 기여도 |
        |-------------|-------------|--------|
        | ① 이력 기반 | KALIS-FMS 20~30년 | 40% |
        | ② 설계 기반 | 일송건축 도면 DB | 35% |
        | ③ 구조해석 | 세종대 비선형 FEM | 25% |

        **📊 성능 지표 (TRL 8 실증)**
        - 결함 탐지율: **95%**
        - False Positive: **0건** (Antigravity 보정)
        - 균열 해상도: **0.2 mm** (Y-MaskNet)
        - 보고서 생성: **36분** (vs 3시간)
        """)
        st.info("🎯 TRL 8 → TRL 9 전환 목표: 2026년 LH 파일럿 500세대 실증 완료")

# ══════════════════════════════════════════════════════
# PAGE 7: 클린하우스 마일리지
# ══════════════════════════════════════════════════════
elif page == "🏅 클린하우스 마일리지":
    st.title("🏅 클린하우스 마일리지 제도")
    st.caption("시설물 상태가 양호한 세대에 인센티브 부여 → 입주민 자발적 시설 예방점검 참여 유도")

    st.markdown("""
    > **운영 원리:** 입주민이 앱으로 세대 내부를 자발적으로 점검하고 업로드하면 마일리지 적립.
    > 마일리지가 높은 세대는 관리비 할인, 우선 수리 서비스 등 인센티브 제공.
    > 이를 통해 공급자 중심이 아닌 **입주민 중심 예방형 관리 체계** 완성.
    """)

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("마일리지 참여세대", f"{(mileage_df['앱사용여부']=='사용').sum()}세대",
              help="앱을 사용해 자발적으로 세대 점검에 참여한 가구 수입니다 📱\n"
                   "참여할수록 마일리지가 쌓이고 관리비 할인 혜택을 받습니다.")
    m2.metric("골드 등급", f"{(mileage_df['등급']=='골드').sum()}세대",
              help="1,000점 이상 최우수 참여 세대입니다 🥇\n"
                   "골드 등급은 관리비 20만원 할인 + 우선 수리 서비스 혜택을 받습니다.")
    m3.metric("평균 마일리지", f"{mileage_df['마일리지'].mean():.0f}점",
              help="전체 세대의 평균 마일리지 점수입니다 📊\n\n"
                   "• 1,000점↑: 골드\n• 500~999점: 실버\n• 100~499점: 브론즈\n• 100점↓: 일반")
    m4.metric("인센티브 지급 총액", f"{mileage_df['인센티브_만원'].sum()}만원",
              help="이번 달 전체 참여 세대에 지급된 관리비 할인 혜택 총액입니다 💰\n"
                   "마일리지 등급에 따라 5만~20만원이 자동으로 할인됩니다.")

    tab1, tab2 = st.tabs(["📋 세대별 마일리지 현황", "📊 등급별 분석"])
    with tab1:
        grade_order = {"골드":"🥇 골드","실버":"🥈 실버","브론즈":"🥉 브론즈","일반":"⬜ 일반"}
        disp_m = mileage_df.copy()
        disp_m["등급"] = disp_m["등급"].map(grade_order)
        st.dataframe(disp_m.sort_values("마일리지", ascending=False),
                     use_container_width=True, hide_index=True, height=380)

    with tab2:
        col_a, col_b = st.columns(2)
        with col_a:
            grade_cnt = mileage_df["등급"].value_counts().reset_index()
            grade_cnt.columns = ["등급","세대수"]
            fig = px.bar(grade_cnt, x="등급", y="세대수", height=250,
                         color="등급",
                         color_discrete_map={"골드":"#f59e0b","실버":"#94a3b8","브론즈":"#b45309","일반":"#e5e7eb"},
                         title="등급별 세대 분포", text="세대수")
            fig.update_layout(margin=dict(t=40,b=10), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            fig2 = px.scatter(mileage_df, x="자체점검횟수", y="마일리지",
                              color="등급", height=250,
                              color_discrete_map={"골드":"#f59e0b","실버":"#94a3b8","브론즈":"#b45309","일반":"#94a3b8"},
                              title="자체점검 횟수 vs 마일리지",
                              labels={"자체점검횟수":"연간 자체점검 횟수","마일리지":"누적 마일리지"})
            fig2.update_layout(margin=dict(t=40,b=10))
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    **📌 등급별 혜택:**
    | 등급 | 기준 | 혜택 |
    |------|------|------|
    | 🥇 골드 | 1000점 이상 | 관리비 20만원 할인 + 우선 수리 서비스 |
    | 🥈 실버 | 500~999점 | 관리비 10만원 할인 |
    | 🥉 브론즈 | 100~499점 | 관리비 5만원 할인 |
    | ⬜ 일반 | 100점 미만 | 기본 서비스 |
    """)

# ══════════════════════════════════════════════════════
# PAGE 8: Vision 2030 예측 분석
# ══════════════════════════════════════════════════════
elif page == "🔮 Vision 2030 예측분석":
    st.title("🔮 Vision 2030 — AI 예측 분석")
    st.caption("머신러닝 기반 고장 예측 (30% 감소) · 회귀분석 에너지 최적화 (15% 절감) · 공실 예측")

    tab1, tab2, tab3, tab4 = st.tabs(["⚙ 고장 예측 (ML)", "⚡ 에너지 최적화", "🏠 공실 예측", "📈 사업화 KPI"])

    with tab1:
        st.markdown('<div class="sh">⚙ 머신러닝 기반 설비 고장 예측 (AI 적용 전·후 비교)</div>', unsafe_allow_html=True)
        st.info("축적된 IoT 센서 데이터 + 점검 이력을 머신러닝으로 학습 → 향후 12개월 고장 건수 예측\n목표: AI 적용으로 고장 건수 **30% 감소**")

        cpx_sel = st.selectbox("단지 선택", forecast_df["단지"].unique(),
                              help="고장 예측 그래프를 볼 단지를 선택하세요 🏘️\n\n"
                                   "선택하면 해당 단지의 향후 12개월 고장 예측과\n"
                                   "'AI 적용 전'과 '적용 후'를 비교해서 볼 수 있습니다.")
        fc_cpx = forecast_df[forecast_df["단지"] == cpx_sel]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=fc_cpx["예측월"], y=fc_cpx["AI적용전"],
                                 name="AI 적용 전", line=dict(color="#ef4444", dash="dash")))
        fig.add_trace(go.Scatter(x=fc_cpx["예측월"], y=fc_cpx["예상고장건수"],
                                 name="AI 적용 후 (예측)", line=dict(color="#10b981"),
                                 fill="tonexty", fillcolor="rgba(16,185,129,0.1)"))
        fig.add_trace(go.Scatter(
            x=list(fc_cpx["예측월"]) + list(fc_cpx["예측월"])[::-1],
            y=list(fc_cpx["신뢰구간_상"]) + list(fc_cpx["신뢰구간_하"])[::-1],
            fill="toself", fillcolor="rgba(16,185,129,0.08)",
            line=dict(color="rgba(255,255,255,0)"), name="신뢰구간 95%"
        ))
        fig.update_layout(height=350, margin=dict(t=10,b=10),
                          yaxis_title="예상 고장 건수", xaxis_title="월",
                          legend=dict(orientation="h"))
        st.plotly_chart(fig, use_container_width=True)

        reduction = round((fc_cpx["AI적용전"].mean() - fc_cpx["예상고장건수"].mean()) /
                           fc_cpx["AI적용전"].mean() * 100, 1)
        st.success(f"💡 **{cpx_sel} AI 적용 시 고장 건수 예측 감소율: {reduction}%** (목표: 30%)")

    with tab2:
        st.markdown('<div class="sh">⚡ 에너지 최적화 — 회귀분석 기반 비용 절감 예측</div>', unsafe_allow_html=True)
        st.info("전력·열 사용 패턴을 회귀분석 → 비정상 소비 자동 감지 → 절감 권고\n목표: **15% 에너지 비용 절감**")

        months = [(datetime.now() + timedelta(days=30*i)).strftime("%Y-%m") for i in range(12)]
        base_energy = [random.uniform(800, 950) for _ in months]
        opt_energy = [v * random.uniform(0.82, 0.88) for v in base_energy]

        fig2 = go.Figure()
        fig2.add_bar(x=months, y=base_energy, name="현재 전력비 (만원)", marker_color="#f59e0b", opacity=0.7)
        fig2.add_bar(x=months, y=opt_energy, name="AI 최적화 후 (만원)", marker_color="#10b981", opacity=0.85)
        fig2.update_layout(barmode="group", height=320, margin=dict(t=10,b=10),
                           yaxis_title="월 전력비 (만원)")
        st.plotly_chart(fig2, use_container_width=True)

        annual_save = round((sum(base_energy) - sum(opt_energy)) * 12 / 12)
        st.success(f"💡 **연간 에너지 절감 예측: {annual_save:,}만원** ({round(annual_save/sum(base_energy)*100, 1)}% 절감, 목표 15%)")

    with tab3:
        st.markdown('<div class="sh">🏠 공실 예측 모델</div>', unsafe_allow_html=True)
        st.info("계약 만료 이력 + 갱신 의향 + 지역 수요 데이터 → 6개월 내 공실 발생 확률 예측")

        vacancy_data = []
        for cpx in ALL_COMPLEXES:
            vacancy_data.append({
                "단지": cpx[:18] + "..",
                "현재공실": random.randint(0, 8),
                "6개월내_예상공실": random.randint(2, 15),
                "공실발생확률": f"{random.randint(15,65)}%",
                "주요원인": random.choice(["계약만료 집중", "노후시설 기피", "교통 불편", "정상 순환"]),
                "선제조치": random.choice(["입주민 갱신 유도 강화", "시설 개선 우선 배정", "마케팅 강화", "대기자 우선 배정"]),
            })
        st.dataframe(pd.DataFrame(vacancy_data), use_container_width=True, hide_index=True)

        st.markdown("""
        **📌 Vision 2030 목표 요약:**
        | 지표 | 현재 | 2030 목표 | AI 기여 |
        |------|------|-----------|---------|
        | 설비 고장 건수 | 기준 | -30% | 머신러닝 예측정비 |
        | 에너지 비용 | 기준 | -15% | 회귀분석 최적화 |
        | 공실률 | 기준 | -20% | 수요예측·선제대응 |
        | 입주민 만족도 | 기준 | +20% | 앱·마일리지·빠른처리 |
        | 실증 데이터 | 3,847건 | 10,000건 | HSIA 드론·앱 통합 |
        """)

    with tab4:
        st.markdown('<div class="sh">📈 연차별 사업화 목표 및 KPI — LH 500억 시장 수주 로드맵</div>', unsafe_allow_html=True)
        st.info("AX-SPRINT 과제 종료 후 LH 전국 공공임대주택 확산 전략 | 1차년도 5억 → 2차년도 25억 → LH 500억 시장")

        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        kpi_col1.metric("1차년도 목표", "5억 원", "SH·GBDC 실증 수주")
        kpi_col2.metric("2차년도 목표", "25억 원", "+400% 성장")
        kpi_col3.metric("LH 시장 규모", "500억 원", "전국 확산")
        kpi_col4.metric("결함 탐지율", "95%", "TRL 9 목표")

        # 연차별 수주 목표 차트
        years_kpi  = ["1차년도\n(2026)", "2차년도\n(2027)", "3차년도\n(2028)", "4차년도\n(2029)", "2030+\nLH 전국"]
        revenue    = [5, 25, 80, 200, 500]
        colors_kpi = ["#6366f1", "#8b5cf6", "#a855f7", "#c084fc", "#10b981"]

        fig_kpi = go.Figure(go.Bar(
            x=years_kpi, y=revenue,
            marker_color=colors_kpi,
            text=[f"{v}억" for v in revenue],
            textposition="outside"
        ))
        fig_kpi.update_layout(height=320, margin=dict(t=30, b=10),
                              yaxis_title="수주 목표 (억 원)",
                              title="연차별 누적 수주 목표")
        st.plotly_chart(fig_kpi, use_container_width=True)

        st.markdown("""
        **📋 연차별 세부 KPI**
        | 구분 | 1차년도 (2026) | 2차년도 (2027) | LH 전국 (2030+) |
        |------|---------------|---------------|----------------|
        | 수주 목표 | **5억** | **25억** | **500억** |
        | 적용 단지 | SH 5개 + GBDC 2개 | 광역 공사 확산 | LH 전국 |
        | 결함 탐지율 | 90% (TRL 8) | 95% (TRL 9) | 97%+ |
        | 보고서 단축 | 60% (3h→72분) | **80% (3h→36분)** | 90%+ |
        | False Positive | < 5건 | **0건** | 0건 |
        | HISIA 표준 | 참여 | **표준 등재** | 글로벌 확산 |
        | 실증 데이터 | 3,847건 | 10,000건 | 50,000건+ |

        **🏆 핵심 기술 경쟁력 (기술적 해자)**
        - **KALIS-FMS 30년 이력** — 경쟁사 대비 10년 이상 데이터 선점
        - **Antigravity 오탐 보정** — False Positive 0건, 업계 유일 3중 교차검증
        - **법무법인 수호 자문** — AI 보고서 공문서 효력, 전자문서법 근거
        - **세종대 비선형 FEM** — 학계 검증된 구조 해석 모듈, 특허 출원 예정
        - **HISIA 드론 표준** — 표준 제정 참여로 후발 진입장벽 형성
        """)

# ══════════════════════════════════════════════════════
# PAGE 9: AI 데이터 파이프라인
# ══════════════════════════════════════════════════════
elif page == "🧬 AI 데이터 파이프라인":
    st.title("🧬 AI 데이터 파이프라인 — 학습 데이터셋 완전 명세")
    st.caption("RAW 데이터 → 학습 데이터 → AI 모델 → 분석 결과 → 현장 활용 → 기대 효과 | 55개 샘플 데이터 파이프라인")

    st.markdown("""
    > **이 페이지는 에이톰-AX 플랫폼의 전체 AI 서비스가 어떤 데이터로, 어떤 AI 모델을 거쳐,
    > 어떤 결과를 내고, 현장에서 어떻게 쓰이는지를 55개 실증 파이프라인으로 보여줍니다.**
    >
    > 사업계획서 4장 '추진 전략 및 계획'의 기술적 근거 자료입니다.
    """)

    # ── 파이프라인 흐름도 (Plotly 시각화) ──
    st.markdown('<div class="sh">🔄 AI 데이터 처리 6단계 파이프라인</div>', unsafe_allow_html=True)

    fig_pipe = go.Figure()

    # 단계 정의
    stages = [
        {"num": "①", "title": "RAW 데이터", "color": "#6366f1",
         "items": ["드론 4K 이미지", "IoT 센서 시계열", "민원 텍스트/사진", "BIM·LiDAR 3D", "GPR·InSAR"],
         "icon": "📥", "count": "10종"},
        {"num": "②", "title": "학습 데이터", "color": "#8b5cf6",
         "items": ["COCO 라벨링", "이상/정상 태깅", "NER·감성 라벨", "시계열 윈도우", "증강·전처리"],
         "icon": "🏷", "count": "55건"},
        {"num": "③", "title": "AI 모델", "color": "#0ea5e9",
         "items": ["Y-MaskNet (F1=0.97)", "LSTM·ARIMA", "XGBoost·LightGBM", "KoBERT·LLM+RAG", "PINN·PointNet++"],
         "icon": "🧠", "count": "25종+"},
        {"num": "④", "title": "분석 결과", "color": "#14b8a6",
         "items": ["균열 0.2mm 탐지", "이상징후 경보", "위험도 스코어링", "자동 분류·예측", "구조 시뮬레이션"],
         "icon": "📊", "count": "실시간"},
        {"num": "⑤", "title": "현장 활용", "color": "#f59e0b",
         "items": ["긴급 보수 지시", "담당자 자동 배정", "FMS 자동 전송", "보고서 자동 생성", "대피·소방 연계"],
         "icon": "🏗", "count": "자동화"},
        {"num": "⑥", "title": "기대 효과", "color": "#10b981",
         "items": ["대형사고 0건", "비용 70% 절감", "처리시간 80%↓", "만족도 20%↑", "ROI 340%"],
         "icon": "🎯", "count": "검증완료"},
    ]

    box_w, box_h = 1.4, 1.0
    gap = 0.55
    y_center = 0.5
    total_w = len(stages) * box_w + (len(stages) - 1) * gap

    for i, s in enumerate(stages):
        x = i * (box_w + gap)

        # 박스 배경 (라운드 사각형 시뮬레이션)
        fig_pipe.add_shape(
            type="rect", x0=x, y0=y_center - box_h/2, x1=x + box_w, y1=y_center + box_h/2,
            fillcolor=s["color"], opacity=0.12, line=dict(color=s["color"], width=2.5),
            layer="below"
        )

        # 상단 번호 + 제목 배지
        fig_pipe.add_shape(
            type="rect",
            x0=x + 0.05, y0=y_center + box_h/2 - 0.22,
            x1=x + box_w - 0.05, y1=y_center + box_h/2 - 0.02,
            fillcolor=s["color"], opacity=0.85, line=dict(width=0),
            layer="below"
        )
        fig_pipe.add_annotation(
            x=x + box_w/2, y=y_center + box_h/2 - 0.12,
            text=f"<b>{s['icon']} {s['num']} {s['title']}</b>",
            font=dict(size=12, color="white", family="Arial"),
            showarrow=False
        )

        # 건수 배지
        fig_pipe.add_annotation(
            x=x + box_w/2, y=y_center + box_h/2 + 0.08,
            text=f"<b>{s['count']}</b>",
            font=dict(size=9, color=s["color"], family="Arial"),
            showarrow=False,
            bgcolor="white", bordercolor=s["color"], borderwidth=1, borderpad=2
        )

        # 항목 리스트
        items_text = "<br>".join([f"• {item}" for item in s["items"]])
        fig_pipe.add_annotation(
            x=x + box_w/2, y=y_center - 0.12,
            text=f"<span style='font-size:10px;color:#374151;'>{items_text}</span>",
            font=dict(size=10, color="#374151", family="Arial"),
            showarrow=False, align="left"
        )

        # 화살표 (단계 간 연결)
        if i < len(stages) - 1:
            ax_start = x + box_w + 0.03
            ax_end = (i + 1) * (box_w + gap) - 0.03
            fig_pipe.add_annotation(
                x=ax_end, y=y_center + 0.15,
                ax=ax_start, ay=y_center + 0.15,
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True,
                arrowhead=3, arrowsize=1.2, arrowwidth=2.5,
                arrowcolor="#94a3b8"
            )

    # MLOps 피드백 루프 (하단 곡선 화살표)
    loop_y = y_center - box_h/2 - 0.18
    fig_pipe.add_shape(
        type="line",
        x0=5 * (box_w + gap) + box_w/2, y0=y_center - box_h/2,
        x1=5 * (box_w + gap) + box_w/2, y1=loop_y,
        line=dict(color="#ef4444", width=2, dash="dot")
    )
    fig_pipe.add_shape(
        type="line",
        x0=5 * (box_w + gap) + box_w/2, y0=loop_y,
        x1=box_w/2, y1=loop_y,
        line=dict(color="#ef4444", width=2, dash="dot")
    )
    fig_pipe.add_annotation(
        x=box_w/2, y=loop_y,
        ax=box_w/2 + 0.3, ay=loop_y,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=3, arrowsize=1.2, arrowwidth=2,
        arrowcolor="#ef4444"
    )
    fig_pipe.add_annotation(
        x=total_w / 2, y=loop_y - 0.07,
        text="<b>🔄 MLOps 피드백 루프 — 결과 → 재학습 → 모델 지속 개선</b>",
        font=dict(size=10, color="#ef4444", family="Arial"),
        showarrow=False, bgcolor="rgba(239,68,68,0.08)", borderpad=3
    )

    fig_pipe.update_layout(
        height=380, margin=dict(t=10, b=30, l=10, r=10),
        xaxis=dict(visible=False, range=[-0.3, total_w + 0.3]),
        yaxis=dict(visible=False, range=[loop_y - 0.18, y_center + box_h/2 + 0.22]),
        plot_bgcolor="white", paper_bgcolor="white",
        showlegend=False
    )
    st.plotly_chart(fig_pipe, use_container_width=True)

    # ── KPI 요약 ──
    pk1, pk2, pk3, pk4, pk5 = st.columns(5)
    with pk1:
        st.markdown('<div class="kpi-card"><div class="label">총 파이프라인</div><div class="value">55개</div><div class="sub">9개 카테고리</div></div>', unsafe_allow_html=True)
    with pk2:
        st.markdown('<div class="kpi-card-green"><div class="label">AI 모델 종류</div><div class="value">25+</div><div class="sub">CNN·LSTM·XGB·LLM 등</div></div>', unsafe_allow_html=True)
    with pk3:
        st.markdown('<div class="kpi-card"><div class="label">데이터 소스</div><div class="value">10종</div><div class="sub">이미지·센서·텍스트·3D</div></div>', unsafe_allow_html=True)
    with pk4:
        st.markdown('<div class="kpi-card-amber"><div class="label">현장 적용</div><div class="value">100%</div><div class="sub">전 파이프라인 실증 가능</div></div>', unsafe_allow_html=True)
    with pk5:
        st.markdown('<div class="kpi-card-green"><div class="label">예상 ROI</div><div class="value">340%</div><div class="sub">투자 회수 8개월</div></div>', unsafe_allow_html=True)

    st.divider()

    # ── 카테고리별 필터 ──
    st.markdown('<div class="sh">📋 55개 AI 파이프라인 데이터셋 (카테고리별 탐색)</div>', unsafe_allow_html=True)

    categories = sorted(pipeline_df["분류"].unique())
    cat_labels = {
        "비전AI-이미지": "🖼 비전AI — 드론·앱 시설물 손상 이미지 (10건)",
        "IoT-센서": "📡 IoT 센서 — 온도·CO·진동·습도·전력 (6건)",
        "IoT-LiDAR": "📡 IoT LiDAR — 3D 점군 데이터 (2건)",
        "민원-NLP": "📋 민원 NLP — 텍스트 자동분류 (2건)",
        "민원-분석": "📋 민원 분석 — 발생 예측 (1건)",
        "민원-감성": "📋 민원 감성분석 (1건)",
        "민원-이미지": "📋 민원 이미지 분류 (1건)",
        "민원-예측": "📋 민원 처리시간 예측 (1건)",
        "DigitalTwin-3D": "🏗 Digital Twin — 3D 구조 (1건)",
        "DigitalTwin-시뮬": "🏗 Digital Twin — 시뮬레이션 (1건)",
        "DigitalTwin-에너지": "🏗 Digital Twin — 에너지 (1건)",
        "DigitalTwin-노후": "🏗 Digital Twin — 노후도 (1건)",
        "DigitalTwin-배관": "🏗 Digital Twin — 배관 (1건)",
        "DigitalTwin-화재": "🏗 Digital Twin — 화재 (1건)",
        "이상징후-복합": "🚨 이상징후 — 복합 센서 (1건)",
        "이상징후-진동": "🚨 이상징후 — 진동 (1건)",
        "이상징후-전력": "🚨 이상징후 — 전력 (1건)",
        "이상징후-가스": "🚨 이상징후 — 가스 (1건)",
        "이상징후-수위": "🚨 이상징후 — 수위 (1건)",
        "선제탐지-균열": "🛡 선제탐지 — 균열 진행 (1건)",
        "선제탐지-배관": "🛡 선제탐지 — 배관 (1건)",
        "선제탐지-외벽": "🛡 선제탐지 — 외벽 (1건)",
        "선제탐지-승강기": "🛡 선제탐지 — 승강기 (1건)",
        "선제탐지-방수": "🛡 선제탐지 — 방수 (1건)",
        "RPA-관리비": "🤖 RPA — 관리비 (1건)",
        "RPA-계약": "🤖 RPA — 계약 (1건)",
        "RPA-점검": "🤖 RPA — 점검 (1건)",
        "RPA-민원배정": "🤖 RPA — 민원배정 (1건)",
        "RPA-보고서": "🤖 RPA — 보고서 (1건)",
        "RPA-고지": "🤖 RPA — 고지 (1건)",
        "RPA-에너지": "🤖 RPA — 에너지 (1건)",
        "예방조치-구조": "🔰 예방조치 — 구조 (1건)",
        "예방조치-화재": "🔰 예방조치 — 화재 (1건)",
        "예방조치-누수": "🔰 예방조치 — 누수 (1건)",
        "예방조치-지반": "🔰 예방조치 — 지반 (1건)",
        "예방조치-종합": "🔰 예방조치 — 종합 (1건)",
        "대시보드-KPI": "📊 대시보드 — KPI (1건)",
        "대시보드-예측": "📊 대시보드 — 예측 (1건)",
        "대시보드-ROI": "📊 대시보드 — ROI (1건)",
    }

    # 상위 카테고리 그룹
    category_groups = {
        "🖼 비전AI·드론 (10건)": [c for c in categories if c.startswith("비전AI")],
        "📡 IoT·LiDAR (8건)": [c for c in categories if c.startswith("IoT")],
        "📋 민원 데이터 (6건)": [c for c in categories if c.startswith("민원")],
        "🏗 Digital Twin (6건)": [c for c in categories if c.startswith("DigitalTwin")],
        "🚨 이상징후 감지 (5건)": [c for c in categories if c.startswith("이상징후")],
        "🛡 선제 탐지 (5건)": [c for c in categories if c.startswith("선제탐지")],
        "🤖 RPA 행정자동화 (7건)": [c for c in categories if c.startswith("RPA")],
        "🔰 예방조치 (5건)": [c for c in categories if c.startswith("예방조치")],
        "📊 대시보드 분석 (3건)": [c for c in categories if c.startswith("대시보드")],
    }

    selected_group = st.selectbox(
        "카테고리 선택",
        list(category_groups.keys()),
        help="보고 싶은 데이터 카테고리를 선택하세요.\n각 카테고리별로 RAW→학습→모델→결과→활용→효과 파이프라인을 확인할 수 있습니다."
    )
    selected_cats = category_groups[selected_group]
    filtered_df = pipeline_df[pipeline_df["분류"].isin(selected_cats)]

    st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=400)

    # ── 상세 파이프라인 카드 ──
    st.markdown("---")
    st.markdown(f"### 📌 {selected_group} — 상세 파이프라인")

    for _, row in filtered_df.iterrows():
        with st.expander(f"**{row['ID']}** | {row['분류']} — {row['RAW데이터'][:40]}..."):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"""
**① RAW 데이터**
> {row['RAW데이터']}

**② 학습 데이터**
> {row['학습데이터']}

**③ AI 모델**
> {row['AI모델']}
                """)
            with col_b:
                st.markdown(f"""
**④ 분석 결과**
> {row['결과']}

**⑤ 현장 활용**
> {row['활용']}

**⑥ 기대 효과**
> {row['효과']}
                """)

    # ── 전체 통계 ──
    st.markdown("---")
    st.markdown('<div class="sh">📊 AI 파이프라인 카테고리별 분포</div>', unsafe_allow_html=True)

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        # 상위 카테고리별 건수
        group_counts = []
        for grp, cats in category_groups.items():
            cnt = pipeline_df[pipeline_df["분류"].isin(cats)].shape[0]
            group_counts.append({"카테고리": grp.split("(")[0].strip(), "건수": cnt})
        grp_df = pd.DataFrame(group_counts)
        fig_grp = px.bar(grp_df, x="건수", y="카테고리", orientation="h", height=350,
                         color="건수", color_continuous_scale="Viridis",
                         title="카테고리별 파이프라인 건수")
        fig_grp.update_layout(margin=dict(t=40, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig_grp, use_container_width=True)

    with col_chart2:
        fig_pie = px.pie(grp_df, values="건수", names="카테고리", height=350,
                         title="카테고리 비율", hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Set3)
        fig_pie.update_layout(margin=dict(t=40, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── AI 모델 현황 ──
    st.markdown('<div class="sh">🤖 적용 AI 모델 현황</div>', unsafe_allow_html=True)
    st.markdown("""
    | AI 모델 카테고리 | 주요 모델 | 적용 영역 | 핵심 성능 |
    |-----------------|----------|-----------|----------|
    | **비전 AI** | Y-MaskNet (Mask R-CNN), EfficientNet, PointNet++ | 균열·누수·드라이비트·박락 탐지 | F1=0.97, mAP≥0.92 |
    | **시계열 예측** | LSTM, ARIMA, Seasonal ARIMA | 균열 성장, 센서 이상, 침하 예측 | RMSE 2.1건, MAE 0.3일 |
    | **이상 탐지** | AutoEncoder, Isolation Forest, PCA | IoT 센서 이상, 전력 이상, 배관 전조 | False Positive ≤5% |
    | **앙상블 학습** | XGBoost, LightGBM, Random Forest, Stacking | 위험도 예측, 민원 예측, 연체 예측 | AUC≥0.85 |
    | **자연어 처리** | KoBERT, LLM + RAG | 민원 분류, 감성분석, 보고서 생성 | Acc=0.92 |
    | **3D/공간** | PointNet++, ICP, FDS, PINN | Digital Twin, 구조 해석, 화재 시뮬 | IoU=0.88 |
    | **최적화** | RL, Hungarian Algorithm, Portfolio Risk | HVAC 제어, 담당자 배정, 예산 배분 | ROI 340% |
    """)

    st.info("""
    **📌 데이터 파이프라인 핵심 원칙:**
    1. **End-to-End 연계** — 모든 RAW 데이터가 최종 현장 조치까지 자동으로 흐름
    2. **XAI 투명성** — AI 판정 근거(SHAP)를 항상 함께 제공하여 현장 신뢰 확보
    3. **Antigravity 보정** — KALIS-FMS 30년 이력 + 일송 설계 + 세종대 FEM 3중 검증으로 오탐 0건
    4. **실시간 피드백** — 결과가 다시 학습 데이터로 환류 → 모델 지속 개선 (MLOps)
    """)

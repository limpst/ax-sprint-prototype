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
    ], label_visibility="collapsed")

    st.divider()
    st.markdown("**수요처 선택**")
    demand_site = st.radio("", ["SH 서울주택도시공사", "경상북도개발공사"],
                           label_visibility="collapsed")
    cpx_list = COMPLEXES_SH if "SH" in demand_site else COMPLEXES_GB
    selected_cpx = st.selectbox("단지 선택", cpx_list)

    st.divider()
    st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.caption("국토교통부 AX-SPRINT 과제")
    st.caption("TRL 8 수준 · 현장실증 중")

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
                                   horizontal=True)
            uploaded = st.file_uploader("이미지 업로드", type=["jpg","jpeg","png"])

            st.divider()
            sample = st.selectbox("또는 샘플 시나리오 선택", [
                "① 수직균열 0.35mm — 외벽 3층 (고위험)",
                "② 누수흔적 — 지하 1층 천장 (중위험)",
                "③ 드라이비트 화재취약 — 외벽 전면 (고위험)",
                "④ 옥상 박리손상 2.1mm (고위험)",
                "⑤ 수평균열 0.08mm — 계단실 (저위험)",
            ])
            run_btn = st.button("🤖 Y-MaskNet 분석 실행", type="primary", use_container_width=True)

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
                r1.metric("탐지 유형", sc["유형"])
                r2.metric("AI 신뢰도", f"{int(sc['신뢰']*100)}%")
                r3.metric("위험도", f"{'🔴' if sc['위험']=='고' else '🟡' if sc['위험']=='중' else '🟢'} {sc['위험']}")
                r4.metric("손상폭", f"{sc['폭']} mm" if sc['폭'] > 0 else "면적 분석")

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
        risk_f = st.multiselect("위험도 필터", ["고","중","저"], default=["고","중","저"], key="dmg_risk")
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
        b1.metric("총 발행 세대", f"{len(billing_df):,}세대")
        b2.metric("자동발행 완료", f"{(billing_df['발행상태']=='자동발행완료').sum():,}건")
        b3.metric("오류 확인필요", f"{(billing_df['발행상태']=='오류확인필요').sum()}건", delta="수동처리 필요", delta_color="inverse")
        b4.metric("자동화율", "80.0%", delta="목표 달성", delta_color="normal")

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
        cc1.metric("전체 계약", f"{len(contract_df)}건")
        cc2.metric("60일내 만료", f"{len(soon)}건", delta="알림발송 완료", delta_color="normal")
        cc3.metric("이미 만료", f"{len(urgent)}건", delta="갱신협의 진행중", delta_color="inverse")

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

        gen_schedule = st.button("🤖 AI 점검 일정 자동 생성", type="primary")
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
                                          default=list(COMPLAINT_TYPES.keys()), key="c1")
        with f2: f_risk = st.multiselect("위험도", ["고","중","저"],
                                          default=["고","중","저"], key="c2")
        with f3: f_stat = st.multiselect("상태", complaint_df["상태"].unique().tolist(),
                                          default=complaint_df["상태"].unique().tolist(), key="c3")
        with f4: f_site = st.multiselect("수요처", ["SH공사","경북개발공사"],
                                          default=["SH공사","경북개발공사"], key="c4")

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
                nc_site = st.selectbox("수요처", ["SH공사","경북개발공사"])
                nc_cpx = st.selectbox("단지", ALL_COMPLEXES)
                nc_unit = st.text_input("호수", placeholder="예: 101동 302호")
                nc_type = st.selectbox("손상 유형", list(COMPLAINT_TYPES.keys()))
            with r2:
                nc_loc = st.text_input("손상 위치", placeholder="예: 화장실 천장, 주방 수전 하단")
                nc_desc = st.text_area("상세 설명", placeholder="언제부터 생겼는지, 어느 정도 심한지 등", height=90)
                nc_photo = st.file_uploader("사진 첨부", type=["jpg","jpeg","png"])
            submit_c = st.form_submit_button("📤 민원 접수하기", type="primary", use_container_width=True)

        if submit_c:
            with st.spinner("AI 분류 엔진 분석 중..."):
                time.sleep(1.3)
            info = COMPLAINT_TYPES[nc_type]
            new_num = f"CM-2026-{random.randint(2000,9999)}"
            ai_score = round(random.uniform(0.78, 0.97), 2)
            st.success(f"✅ 민원 접수 완료 — **{new_num}**")
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("민원번호", new_num)
            m2.metric("AI 위험도 판정", f"{'🔴' if info['위험도']=='고' else '🟡' if info['위험도']=='중' else '🟢'} {info['위험도']}")
            m3.metric("AI 신뢰도", f"{int(ai_score*100)}%")
            m4.metric("RPA 자동화율", f"{info['rpa자동화']}%")
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

    def sensor_kpi(col, name, val, unit, thr, higher_bad=True):
        over = (val > thr) if higher_bad else (val < thr)
        badge = "🔴 경고" if over else "🟢 정상"
        with col:
            st.metric(f"{name} {badge}", f"{val:.1f}{unit}", delta=f"기준 {thr}{unit}",
                      delta_color="inverse" if over else "off")

    sensor_kpi(c1, "온도",   latest["온도"],   "°C",  30)
    sensor_kpi(c2, "습도",   latest["습도"],   "%",   70)
    sensor_kpi(c3, "전력",   latest["전력_kWh"],"kWh", 4.0)
    sensor_kpi(c4, "진동",   latest["진동_g"], "g",   0.5)
    sensor_kpi(c5, "CO농도", latest["CO_ppm"], "ppm", 10)

    st.divider()
    period = st.slider("조회 기간 (일)", 1, 30, 7)
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
        selected_prev = st.selectbox("단지 선택", [r["단지"] for r in prevention_data])
        row = next(r for r in prevention_data if r["단지"] == selected_prev)
        st.metric("위험도 점수", f"{row['위험도 점수']}점", delta=row["등급"])

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
            prev_cpx = st.selectbox("단지", ALL_COMPLEXES)
            prev_facility = st.selectbox("시설 유형", ["외벽 (드라이비트)", "배관·누수", "전기 설비", "지붕·옥상", "공용 계단·복도"])
        with p2:
            prev_priority = st.selectbox("우선순위", ["🔴 긴급 (48시간 내)", "🟡 우선 (1주 내)", "🟢 일반 (1개월 내)"])
            prev_worker = st.text_input("담당 업체", placeholder="예) ○○유지보수")
        gen_prev = st.form_submit_button("🛡 예방 정비 지시서 생성", type="primary", use_container_width=True)

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
    m1.metric("마일리지 참여세대", f"{(mileage_df['앱사용여부']=='사용').sum()}세대")
    m2.metric("골드 등급", f"{(mileage_df['등급']=='골드').sum()}세대")
    m3.metric("평균 마일리지", f"{mileage_df['마일리지'].mean():.0f}점")
    m4.metric("인센티브 지급 총액", f"{mileage_df['인센티브_만원'].sum()}만원")

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

    tab1, tab2, tab3 = st.tabs(["⚙ 고장 예측 (ML)", "⚡ 에너지 최적화", "🏠 공실 예측"])

    with tab1:
        st.markdown('<div class="sh">⚙ 머신러닝 기반 설비 고장 예측 (AI 적용 전·후 비교)</div>', unsafe_allow_html=True)
        st.info("축적된 IoT 센서 데이터 + 점검 이력을 머신러닝으로 학습 → 향후 12개월 고장 건수 예측\n목표: AI 적용으로 고장 건수 **30% 감소**")

        cpx_sel = st.selectbox("단지 선택", forecast_df["단지"].unique())
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

"""
에이톰-AX UI 공통 모듈 · Atom-AX shared UI helpers (v2.5)

- T(ko, en): 현재 언어로 문자열 선택 · pick string by current language
- 축 라벨 사전 AXIS: 컬럼명 → 「무엇을 (단위)」 KR/EN · column → plain "what (unit)" label
- plotly_chart(): st.plotly_chart 를 감싸 축 제목을 바꾸고, 제목 없는 축을 기록한다
- kpi(): KPI 카드 공통 컴포넌트
- 캐시된 엔진 · 검증 · 문장 분류기 로더
"""
from __future__ import annotations

import streamlit as st

_orig_plotly_chart = st.plotly_chart

LANGS = {"ko": "한국어", "en": "English"}


def lang() -> str:
    return st.session_state.get("lang", "ko")


def T(ko: str, en: str) -> str:
    return en if lang() == "en" else ko


def init_lang():
    """?lang=en 쿼리로 언어를 기억한다 · remember language in the URL query."""
    if "lang" not in st.session_state:
        q = st.query_params.get("lang", "ko")
        st.session_state.lang = q if q in LANGS else "ko"


def lang_switch():
    cur = lang()
    choice = st.radio("Language · 언어", list(LANGS), index=list(LANGS).index(cur),
                      format_func=lambda k: LANGS[k], horizontal=True, key="_lang_radio")
    if choice != cur:
        st.session_state.lang = choice
        st.query_params["lang"] = choice
        st.rerun()


# ── 메뉴 · menu (내부 키는 한국어 고정 · internal keys stay Korean) ──
PAGES = [
    ("📊 통합 대시보드", "📊 Integrated dashboard"),
    ("✈ 비전AI · 드론 정밀진단", "✈ Vision AI · drone diagnosis"),
    ("🤖 RPA 행정 자동화", "🤖 RPA admin automation"),
    ("📋 AI 민원 관리", "📋 AI complaint management"),
    ("📡 IoT · 디지털 트윈", "📡 IoT · digital twin"),
    ("🛡 AI 사전 예방 정비", "🛡 AI preventive maintenance"),
    ("🏅 클린하우스 마일리지", "🏅 Clean-house mileage"),
    ("🔮 Vision 2030 예측분석", "🔮 Vision 2030 forecasting"),
    ("🧬 AI 데이터 파이프라인", "🧬 AI data pipeline"),
    ("📐 모델 성능 · 검증", "📐 Model performance · validation"),
]
PAGE_EN = dict(PAGES)


def page_label(k: str) -> str:
    return T(k, PAGE_EN.get(k, k))


# ── 축 라벨 사전 · axis-label dictionary  {원래 제목: (KR, EN)} ──
AXIS = {
    # 공통 · common
    "건수": ("건수 (건)", "Count (cases)"),
    "count": ("건수 (건)", "Count (cases)"),
    "value": ("값", "Value"),
    "index": ("순번", "Index"),
    "variable": ("항목", "Item"),
    "단지": ("단지", "Housing complex"),
    "유형": ("유형", "Type"),
    "상태": ("처리 상태", "Status"),
    "월": ("월 (1~12)", "Month (1–12)"),
    "ts": ("시각", "Time"),
    "시간": ("경과 시간 (시간)", "Elapsed time (hours)"),
    "등급": ("등급", "Tier"),
    "세대수": ("세대 수 (세대)", "Households"),
    "중요도": ("중요도 (0~1, 합 1)", "Importance (0–1, sums to 1)"),
    "특징": ("입력 feature", "Input feature"),
    # 대시보드 · dashboard
    "노후도점수": ("건전도 점수 (0~100, 높을수록 상태 좋음)", "Condition score (0–100, higher = better)"),
    "건전도 점수": ("건전도 점수 (0~100, 높을수록 상태 좋음)", "Condition score (0–100, higher = better)"),
    "경과년수": ("준공 후 지난 햇수 (년)", "Years since completion"),
    "연간 절감 (만원)": ("1년에 아끼는 돈 (만원)", "Annual saving (KRW 10k)"),
    "항목": ("항목", "Item"),
    # 비전 · vision
    "탐지방법": ("탐지 방법", "Detection method"),
    "균열폭_mm": ("균열 폭 (mm)", "Crack width (mm)"),
    "면적_cm2": ("손상 면적 (cm²)", "Damage area (cm²)"),
    "위험점수": ("위험 점수 (높을수록 위험)", "Risk score (higher = riskier)"),
    # RPA · billing
    "관리비_만원": ("관리비 (만원)", "Management fee (KRW 10k)"),
    "업무": ("행정 업무", "Admin task"),
    "자동화율": ("자동화율 (%)", "Automation rate (%)"),
    "면적_m2": ("전용 면적 (m²)", "Unit area (m²)"),
    "총청구_만원": ("총 청구액 (만원)", "Total bill (KRW 10k)"),
    "연체개월": ("연체 개월 수 (개월)", "Months overdue"),
    # 민원 · complaints
    "처리일수": ("처리에 걸린 날 (일)", "Days to resolve"),
    # 마일리지 · mileage
    "자체점검횟수": ("입주민 자체 점검 횟수 (회)", "Resident self-checks (times)"),
    "마일리지": ("마일리지 (점)", "Mileage (points)"),
    # 파이프라인 · pipeline
    "월차": ("관측 개월 (개월)", "Months observed"),
    "GPR공동크기_cm": ("GPR 로 찾은 땅속 빈 공간 크기 (cm)", "GPR-detected void size (cm)"),
    "침하확률": ("땅 꺼짐 확률 (0~1)", "Subsidence probability (0–1)"),
    "관로경과년수": ("배관 설치 후 햇수 (년)", "Pipe age (years)"),
    # 코드에 직접 적힌 축 제목 · titles written in app.py
    "RPA 자동화율 (%)": ("RPA 자동화율 (%)", "RPA automation rate (%)"),
    "처리 기간 (일)": ("처리 기간 (일)", "Days to resolve"),
    "경과 년수": ("준공 후 지난 햇수 (년)", "Years since completion"),
    "구조 건전도 지수": ("구조 건전도 지수 (높을수록 튼튼)", "Structural health index (higher = sounder)"),
    "연간 자체점검 횟수": ("1년 동안 입주민 자체 점검 횟수 (회)", "Resident self-checks per year (times)"),
    "누적 마일리지": ("누적 마일리지 (점)", "Cumulative mileage (points)"),
    "예상 고장 건수": ("예상 고장 건수 (건/월)", "Expected failures (cases/month)"),
    "월 전력비 (만원)": ("월 전력비 (만원)", "Monthly power cost (KRW 10k)"),
    "수주 목표 (억 원)": ("수주 목표 (억 원)", "Order target (KRW 100 M)"),
    "측정 시각": ("측정 시각", "Time"),
}

_missing: list = []


def _relabel(axis):
    t = axis.title.text if axis.title and axis.title.text else None
    if t is None:
        return False
    if t in AXIS:
        axis.title.text = T(*AXIS[t])
    return True


def plotly_chart(fig, *args, **kwargs):
    """축 제목을 언어별 라벨로 바꾸고 제목 없는 축을 기록 · relabel axes, record unlabeled ones."""
    try:
        lay = fig.layout
        for name in list(lay):
            if name.startswith(("xaxis", "yaxis")):
                ax = lay[name]
                if ax.visible is False:
                    continue
                if not _relabel(ax):
                    _missing.append((st.session_state.get("_cur_page", "?"), name,
                                     (lay.title.text if lay.title and lay.title.text else "")))
    except Exception:
        pass
    return _orig_plotly_chart(fig, *args, **kwargs)


def missing_axes():
    return list(_missing)


def axes(fig, x=None, y=None, **more):
    """명시 라벨 지정 · set explicit labels: axes(fig, x=("KR","EN"), y=("KR","EN"))."""
    upd = {}
    if x: upd["xaxis_title_text"] = T(*x)
    if y: upd["yaxis_title_text"] = T(*y)
    for k, v in more.items():
        upd[f"{k}_title_text"] = T(*v)
    fig.update_layout(**upd)
    return fig


def kpi(col, cls, label, value, sub=""):
    col.markdown(f'<div class="{cls}"><div class="label">{label}</div>'
                 f'<div class="value">{value}</div><div class="sub">{sub}</div></div>',
                 unsafe_allow_html=True)


MOBILE_CSS = """
<style>
@media (max-width: 640px) {
  .kpi-card, .kpi-card-green, .kpi-card-red, .kpi-card-amber { padding: 10px !important; margin-bottom: 8px; }
  .kpi-card .value, .kpi-card-green .value, .kpi-card-red .value, .kpi-card-amber .value { font-size: 20px !important; }
  .sh { font-size: 14px !important; }
  h1 { font-size: 1.5rem !important; }
}
.glossary td:first-child { white-space: nowrap; font-weight: 600; }
</style>
"""


# ── 캐시 로더 · cached loaders (서버 프로세스당 1회 · once per server process) ──
@st.cache_resource(show_spinner=False)
def get_engine():
    from ai_pipeline import AXPipelineEngine
    eng = AXPipelineEngine(seed=2026)
    eng.run_all()
    return eng


@st.cache_resource(show_spinner=False)
def get_validation():
    from ai_validation import ValidationSuite
    return ValidationSuite(get_engine(), seed=2026).run_all()


@st.cache_resource(show_spinner=False)
def get_text_model():
    from ai_validation import gen_complaint_texts, make_text_model
    df = gen_complaint_texts(700, 2026)
    return make_text_model(2026).fit(df["문장"].values, df["유형"].values)


@st.cache_resource(show_spinner=False)
def get_xai():
    """6번 페이지용 XAI 만 빠르게 (약 2초) · XAI only, for page 6 (~2 s)."""
    from ai_validation import ValidationSuite
    v = ValidationSuite(get_engine(), seed=2026)
    v.xai()
    return v.out["xai"]


def xai_key(name: str) -> str | None:
    """'SH 강남 매입임대 A (…)' → '강남A동' 식 매핑 · map display name to XAI complex key."""
    for k in ("강남A동", "마포B동", "서초E동", "노원C동", "강서D동", "구미A동", "안동B동"):
        if k[:2] in name:
            return k
    return None

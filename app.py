"""
[국토교통 AX-SPRINT] AI 기반 공공주택 안전관리 플랫폼
에이톰엔지니어링 × 세종대학교 × 한국화재보험협회

실행: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import random
import time
from PIL import Image, ImageDraw
import io
import base64

# ──────────────────────────────────────────
# 전역 설정
# ──────────────────────────────────────────
st.set_page_config(
    page_title="에이톰-AX 공공주택 안전관리 플랫폼",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS 스타일
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
    border-radius: 12px;
    padding: 16px 20px;
    color: white;
    margin-bottom: 12px;
}
.metric-card h4 { margin: 0 0 4px 0; font-size: 13px; opacity: 0.85; }
.metric-card h2 { margin: 0; font-size: 28px; font-weight: 700; }
.metric-card span { font-size: 12px; opacity: 0.75; }

.alert-critical { background:#fee2e2; border-left:4px solid #dc2626; padding:10px 14px; border-radius:6px; margin:6px 0; }
.alert-warning  { background:#fef3c7; border-left:4px solid #d97706; padding:10px 14px; border-radius:6px; margin:6px 0; }
.alert-ok       { background:#d1fae5; border-left:4px solid #059669; padding:10px 14px; border-radius:6px; margin:6px 0; }

.section-header {
    font-size: 18px; font-weight: 700; color: #1e3a5f;
    border-bottom: 2px solid #2563eb;
    padding-bottom: 6px; margin: 20px 0 14px 0;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# 샘플 데이터 생성
# ──────────────────────────────────────────
np.random.seed(42)
random.seed(42)

COMPLEXES = ["강남 매입임대 A동", "서초 매입임대 B동", "마포 영구임대 C단지",
             "노원 국민임대 D단지", "강서 행복주택 E동"]

UNITS = [f"{b}동 {f}층 {u}호" for b in [101, 102, 103] for f in range(2, 8) for u in [1, 2, 3, 4]]


def make_sensor_timeseries(days=30):
    """IoT 센서 시계열 데이터 생성"""
    now = datetime.now()
    records = []
    for d in range(days * 24):
        ts = now - timedelta(hours=(days * 24 - d))
        records.append({
            "timestamp": ts,
            "temperature": 22 + 8 * np.sin(d / 24 * np.pi) + np.random.normal(0, 0.5),
            "humidity": 55 + 15 * np.sin(d / 24 * np.pi + 1) + np.random.normal(0, 1),
            "vibration": abs(np.random.normal(0, 0.3)) + (0.8 if 200 < d < 220 else 0),
            "co_ppm": 2 + abs(np.random.normal(0, 0.3)) + (15 if 400 < d < 410 else 0),
        })
    return pd.DataFrame(records)


def make_complaints():
    """민원 데이터 생성"""
    categories = ["누수", "균열", "화재위험", "시설노후", "기타"]
    statuses = ["접수", "AI분석중", "처리중", "완료"]
    status_weights = [0.15, 0.20, 0.30, 0.35]
    risk_map = {"누수": "중", "균열": "고", "화재위험": "고", "시설노후": "저", "기타": "저"}

    rows = []
    for i in range(60):
        cat = random.choice(categories)
        days_ago = random.randint(0, 90)
        status = random.choices(statuses, weights=status_weights)[0]
        rows.append({
            "민원번호": f"CM-2026-{1000+i}",
            "단지": random.choice(COMPLEXES),
            "세대": random.choice(UNITS),
            "유형": cat,
            "위험도": risk_map[cat],
            "접수일": (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
            "상태": status,
            "처리일수": days_ago if status == "완료" else None,
            "AI점수": round(random.uniform(0.6, 0.99), 2),
        })
    return pd.DataFrame(rows)


def make_inspection_data():
    """점검 이력 데이터 생성"""
    rows = []
    for cpx in COMPLEXES:
        for i in range(12):
            month = datetime.now() - timedelta(days=30 * i)
            rows.append({
                "단지": cpx,
                "점검월": month.strftime("%Y-%m"),
                "균열건수": random.randint(0, 8),
                "누수건수": random.randint(0, 5),
                "화재위험건수": random.randint(0, 3),
                "노후도점수": round(random.uniform(40, 85), 1),
            })
    return pd.DataFrame(rows)


def make_damage_detection_result():
    """AI 손상 탐지 결과 시뮬레이션"""
    results = [
        {"위치": "외벽 3층 북측", "유형": "수직균열", "폭_mm": 0.35, "길이_cm": 42, "위험도": "고", "AI신뢰도": 0.94},
        {"위치": "지하 1층 천장", "유형": "누수흔적", "폭_mm": 0.12, "길이_cm": 18, "위험도": "중", "AI신뢰도": 0.88},
        {"위치": "옥상 방수층", "유형": "박리손상", "폭_mm": 2.10, "길이_cm": 95, "위험도": "고", "AI신뢰도": 0.91},
        {"위치": "계단실 2층", "유형": "수평균열", "폭_mm": 0.08, "길이_cm": 11, "위험도": "저", "AI신뢰도": 0.79},
        {"위치": "외벽 5층 동측", "유형": "표면박락", "폭_mm": 0.55, "길이_cm": 28, "위험도": "중", "AI신뢰도": 0.86},
    ]
    return pd.DataFrame(results)


# 데이터 로딩 (세션 캐싱)
if "sensor_df" not in st.session_state:
    st.session_state.sensor_df = make_sensor_timeseries()
    st.session_state.complaint_df = make_complaints()
    st.session_state.inspection_df = make_inspection_data()
    st.session_state.damage_df = make_damage_detection_result()

sensor_df = st.session_state.sensor_df
complaint_df = st.session_state.complaint_df
inspection_df = st.session_state.inspection_df
damage_df = st.session_state.damage_df

# ──────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────
with st.sidebar:
    st.image("https://via.placeholder.com/220x60/1e3a5f/ffffff?text=ATOM+Engineering", use_container_width=True)
    st.markdown("### 에이톰-AX 플랫폼")
    st.caption("AI 기반 공공주택 안전관리 플랫폼 v1.0")
    st.divider()

    page = st.radio(
        "메뉴",
        ["📊 통합 대시보드", "🔍 AI 손상 탐지", "📡 IoT 실시간 모니터링",
         "📋 민원 관리", "📄 XAI 보고서 생성"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**실증 단지 선택**")
    selected_complex = st.selectbox("", COMPLEXES, label_visibility="collapsed")

    st.divider()
    st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.caption("국토교통부 AX-SPRINT 과제")
    st.caption("주관: (주)에이톰엔지니어링")

# ──────────────────────────────────────────
# PAGE 1: 통합 대시보드
# ──────────────────────────────────────────
if page == "📊 통합 대시보드":
    st.title("🏢 AI 기반 공공주택 안전관리 플랫폼")
    st.caption(f"실증 단지: **{selected_complex}** | 실시간 현황")

    # ── KPI 카드 ──
    col1, col2, col3, col4, col5 = st.columns(5)
    kpis = [
        ("관리 세대수", "2,847 세대", "↑ 12세대 신규"),
        ("이번달 점검완료", "94.2 %", "목표: 95%"),
        ("고위험 민원", "7 건", "▼ 3건 감소"),
        ("AI 탐지 정확도", "93.1 %", "Mask R-CNN 기반"),
        ("평균처리 기간", "4.2 일", "기존 90일 → 4일"),
    ]
    for col, (label, value, sub) in zip([col1, col2, col3, col4, col5], kpis):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <h4>{label}</h4>
                <h2>{value}</h2>
                <span>{sub}</span>
            </div>""", unsafe_allow_html=True)

    # ── 알림 ──
    st.markdown('<div class="section-header">🚨 실시간 위험 알림</div>', unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown('<div class="alert-critical">🔴 <b>강남 A동 3층</b> — 균열 폭 0.35mm 초과 (기준: 0.2mm) | 즉시 점검 필요</div>', unsafe_allow_html=True)
        st.markdown('<div class="alert-warning">🟡 <b>노원 D단지 지하</b> — CO 농도 15ppm 감지 (기준: 10ppm)</div>', unsafe_allow_html=True)
    with col_b:
        st.markdown('<div class="alert-warning">🟡 <b>마포 C단지</b> — 습도 78% 지속 (누수 의심)</div>', unsafe_allow_html=True)
        st.markdown('<div class="alert-ok">🟢 <b>서초 B동</b> — 금일 정기점검 완료 (이상없음)</div>', unsafe_allow_html=True)
    with col_c:
        st.markdown('<div class="alert-critical">🔴 <b>강서 E동 옥상</b> — 방수층 박리 95cm 탐지 (드론 스캔)</div>', unsafe_allow_html=True)
        st.markdown('<div class="alert-ok">🟢 <b>전체 단지</b> — IoT 센서 정상 작동 중 (98.3%)</div>', unsafe_allow_html=True)

    st.divider()

    # ── 차트 행 1 ──
    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.markdown('<div class="section-header">📈 월별 손상 탐지 추이</div>', unsafe_allow_html=True)
        months = [(datetime.now() - timedelta(days=30 * i)).strftime("%Y-%m") for i in range(11, -1, -1)]
        fig = go.Figure()
        fig.add_bar(x=months, y=[random.randint(3, 12) for _ in months], name="균열", marker_color="#ef4444")
        fig.add_bar(x=months, y=[random.randint(1, 7) for _ in months], name="누수", marker_color="#3b82f6")
        fig.add_bar(x=months, y=[random.randint(0, 4) for _ in months], name="화재위험", marker_color="#f59e0b")
        fig.update_layout(barmode="stack", height=280, margin=dict(t=10, b=10), legend=dict(orientation="h"))
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-header">🥧 민원 유형 분포</div>', unsafe_allow_html=True)
        type_counts = complaint_df["유형"].value_counts()
        fig2 = px.pie(values=type_counts.values, names=type_counts.index,
                      color_discrete_sequence=px.colors.qualitative.Set2, height=280)
        fig2.update_layout(margin=dict(t=10, b=10), showlegend=True)
        st.plotly_chart(fig2, use_container_width=True)

    # ── 차트 행 2 ──
    col_l2, col_r2 = st.columns([2, 3])
    with col_l2:
        st.markdown('<div class="section-header">🏗 단지별 노후도 점수</div>', unsafe_allow_html=True)
        avg_age = inspection_df.groupby("단지")["노후도점수"].mean().reset_index()
        avg_age.columns = ["단지", "노후도"]
        avg_age["단지_단축"] = avg_age["단지"].str[:6]
        fig3 = px.bar(avg_age, x="노후도", y="단지_단축", orientation="h",
                      color="노후도", color_continuous_scale="RdYlGn_r", height=280)
        fig3.update_layout(margin=dict(t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col_r2:
        st.markdown('<div class="section-header">📅 민원 처리 현황</div>', unsafe_allow_html=True)
        status_cnt = complaint_df["상태"].value_counts().reset_index()
        status_cnt.columns = ["상태", "건수"]
        color_map = {"접수": "#94a3b8", "AI분석중": "#3b82f6", "처리중": "#f59e0b", "완료": "#10b981"}
        fig4 = px.bar(status_cnt, x="상태", y="건수",
                      color="상태", color_discrete_map=color_map, height=280, text="건수")
        fig4.update_layout(margin=dict(t=10, b=10), showlegend=False)
        fig4.update_traces(textposition="outside")
        st.plotly_chart(fig4, use_container_width=True)

# ──────────────────────────────────────────
# PAGE 2: AI 손상 탐지
# ──────────────────────────────────────────
elif page == "🔍 AI 손상 탐지":
    st.title("🔍 AI 비전 기반 손상 탐지")
    st.caption("Y-MaskNet / Mask R-CNN 기반 인스턴스 세그멘테이션 — 균열·누수·박리 자동 탐지")

    tab1, tab2 = st.tabs(["📸 이미지 분석", "📊 탐지 결과 현황"])

    with tab1:
        col_up, col_res = st.columns([1, 1])

        with col_up:
            st.markdown("**입력 이미지 (드론 촬영 / 입주민 앱 업로드)**")
            uploaded = st.file_uploader("이미지 업로드 (jpg/png)", type=["jpg", "jpeg", "png"])

            st.markdown("또는 **샘플 이미지로 테스트**")
            sample_choice = st.selectbox("샘플 선택", [
                "외벽 균열 (강남 A동 3층)",
                "천장 누수 (마포 C단지 지하)",
                "방수층 박리 (강서 E동 옥상)"
            ])

            analyze_btn = st.button("🤖 AI 분석 실행", type="primary", use_container_width=True)

        with col_res:
            if analyze_btn:
                with st.spinner("AI 모델 추론 중... (Y-MaskNet)"):
                    time.sleep(1.5)

                # 결과 시각화용 가상 이미지 생성
                img = Image.new("RGB", (480, 360), color=(200, 195, 190))
                draw = ImageDraw.Draw(img)

                # 배경 텍스처
                for i in range(0, 480, 40):
                    draw.line([(i, 0), (i, 360)], fill=(180, 175, 170), width=1)
                for j in range(0, 360, 40):
                    draw.line([(0, j), (480, j)], fill=(180, 175, 170), width=1)

                if "균열" in sample_choice:
                    # 균열 시뮬레이션
                    draw.line([(180, 60), (210, 280)], fill=(60, 40, 30), width=3)
                    draw.line([(210, 280), (195, 330)], fill=(60, 40, 30), width=2)
                    # 탐지 박스
                    draw.rectangle([160, 50, 240, 340], outline=(255, 50, 50), width=3)
                    draw.text((162, 35), "균열 0.35mm [94%]", fill=(255, 50, 50))
                    result_type = "수직균열"
                    confidence = 0.94
                    risk = "고"
                    width_mm = 0.35
                    color_risk = "#dc2626"

                elif "누수" in sample_choice:
                    draw.ellipse([120, 100, 320, 250], fill=(140, 160, 175), outline=(50, 100, 200), width=3)
                    draw.text((122, 85), "누수흔적 [88%]", fill=(50, 100, 200))
                    result_type = "누수흔적"
                    confidence = 0.88
                    risk = "중"
                    width_mm = 0.12
                    color_risk = "#d97706"

                else:
                    draw.rectangle([80, 80, 400, 300], fill=(160, 150, 140), outline=(255, 140, 0), width=3)
                    draw.text((82, 65), "박리손상 [91%]", fill=(255, 140, 0))
                    result_type = "방수층 박리"
                    confidence = 0.91
                    risk = "고"
                    width_mm = 2.10
                    color_risk = "#dc2626"

                buf = io.BytesIO()
                img.save(buf, format="PNG")
                st.image(buf.getvalue(), caption="AI 탐지 결과 (세그멘테이션 오버레이)", use_container_width=True)

                st.divider()
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("탐지 유형", result_type)
                c2.metric("AI 신뢰도", f"{confidence*100:.0f}%")
                c3.metric("위험도", risk)
                c4.metric("균열 폭", f"{width_mm} mm")

                if risk == "고":
                    st.error(f"⚠️ **즉시 조치 필요** — 균열 폭 {width_mm}mm 기준치(0.2mm) 초과. 구조 전문가 현장 점검 권고.")
                elif risk == "중":
                    st.warning("⚡ **모니터링 강화** — 30일 이내 재점검 권고.")
                else:
                    st.success("✅ 경미한 손상 — 정기점검 주기 유지.")

                st.markdown("**📋 자동 생성 작업지시서 (Work Order)**")
                wo_data = {
                    "항목": ["단지", "위치", "손상유형", "위험도", "조치기한", "담당부서", "AI분석일"],
                    "내용": [selected_complex, sample_choice, result_type, risk,
                             "즉시" if risk == "고" else "30일 이내",
                             "시설관리팀 1팀", datetime.now().strftime("%Y-%m-%d %H:%M")]
                }
                st.table(pd.DataFrame(wo_data))
            else:
                st.info("👆 좌측에서 이미지를 업로드하거나 샘플을 선택 후 **AI 분석 실행** 버튼을 클릭하세요.")

    with tab2:
        st.markdown('<div class="section-header">📊 전체 손상 탐지 결과</div>', unsafe_allow_html=True)

        risk_filter = st.multiselect("위험도 필터", ["고", "중", "저"], default=["고", "중", "저"])
        filtered = damage_df[damage_df["위험도"].isin(risk_filter)]

        def risk_badge(r):
            colors = {"고": "🔴", "중": "🟡", "저": "🟢"}
            return f"{colors.get(r, '')} {r}"

        display_df = filtered.copy()
        display_df["위험도"] = display_df["위험도"].map(risk_badge)
        st.dataframe(display_df, use_container_width=True, height=250)

        st.markdown('<div class="section-header">📈 손상 유형별 분포</div>', unsafe_allow_html=True)
        fig = px.scatter(damage_df, x="길이_cm", y="폭_mm", size="AI신뢰도",
                         color="위험도", hover_data=["위치", "유형"],
                         color_discrete_map={"고": "#dc2626", "중": "#d97706", "저": "#059669"},
                         labels={"길이_cm": "손상 길이 (cm)", "폭_mm": "손상 폭 (mm)"},
                         height=350)
        st.plotly_chart(fig, use_container_width=True)

# ──────────────────────────────────────────
# PAGE 3: IoT 실시간 모니터링
# ──────────────────────────────────────────
elif page == "📡 IoT 실시간 모니터링":
    st.title("📡 IoT 실시간 환경 모니터링")
    st.caption("온도 · 습도 · 진동 · CO 농도 — 실시간 이상 감지 및 알림")

    # 최신값
    latest = sensor_df.iloc[-1]
    col1, col2, col3, col4 = st.columns(4)

    def sensor_card(col, label, value, unit, threshold, higher_bad=True):
        over = (value > threshold) if higher_bad else (value < threshold)
        status = "🔴 경고" if over else "🟢 정상"
        delta_color = "inverse" if over else "normal"
        with col:
            st.metric(label=f"{label} {status}", value=f"{value:.1f} {unit}",
                      delta=f"기준: {threshold}{unit}", delta_color=delta_color)

    sensor_card(col1, "온도", latest["temperature"], "°C", 30)
    sensor_card(col2, "습도", latest["humidity"], "%", 70)
    sensor_card(col3, "진동", latest["vibration"], "g", 0.5)
    sensor_card(col4, "CO농도", latest["co_ppm"], "ppm", 10)

    st.divider()

    # 시계열 차트
    period = st.slider("조회 기간 (일)", 1, 30, 7)
    cut = datetime.now() - timedelta(days=period)
    view_df = sensor_df[sensor_df["timestamp"] >= cut]

    fig = make_subplots(rows=2, cols=2, subplot_titles=["온도 (°C)", "습도 (%)", "진동 (g)", "CO 농도 (ppm)"])

    fig.add_trace(go.Scatter(x=view_df["timestamp"], y=view_df["temperature"],
                             line=dict(color="#ef4444"), name="온도"), row=1, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="red", row=1, col=1)

    fig.add_trace(go.Scatter(x=view_df["timestamp"], y=view_df["humidity"],
                             line=dict(color="#3b82f6"), name="습도"), row=1, col=2)
    fig.add_hline(y=70, line_dash="dash", line_color="orange", row=1, col=2)

    fig.add_trace(go.Scatter(x=view_df["timestamp"], y=view_df["vibration"],
                             line=dict(color="#8b5cf6"), name="진동"), row=2, col=1)
    fig.add_hline(y=0.5, line_dash="dash", line_color="red", row=2, col=1)

    fig.add_trace(go.Scatter(x=view_df["timestamp"], y=view_df["co_ppm"],
                             line=dict(color="#f59e0b"), name="CO"), row=2, col=2)
    fig.add_hline(y=10, line_dash="dash", line_color="red", row=2, col=2)

    fig.update_layout(height=480, showlegend=False, margin=dict(t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # 이상 이벤트 로그
    st.markdown('<div class="section-header">🚨 이상 감지 이벤트 로그</div>', unsafe_allow_html=True)
    events = [
        {"시간": "2026-04-07 02:14", "센서": "CO 농도", "값": "15.2 ppm", "임계": "10 ppm", "상태": "🔴 경고", "조치": "자동 알림 발송"},
        {"시간": "2026-04-06 18:33", "센서": "진동", "값": "0.82 g", "임계": "0.5 g", "상태": "🔴 경고", "조치": "담당자 문자 발송"},
        {"시간": "2026-04-05 09:21", "센서": "습도", "값": "78.4 %", "임계": "70 %", "상태": "🟡 주의", "조치": "모니터링 강화"},
        {"시간": "2026-04-03 14:05", "센서": "온도", "값": "32.1 °C", "임계": "30 °C", "상태": "🟡 주의", "조치": "환기 권고"},
    ]
    st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)

# ──────────────────────────────────────────
# PAGE 4: 민원 관리
# ──────────────────────────────────────────
elif page == "📋 민원 관리":
    st.title("📋 AI 민원 처리 관리")
    st.caption("RPA 자동화 + AI 우선순위 배정 — 처리기간 90일 → 4일 단축")

    # 요약 지표
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("전체 민원", f"{len(complaint_df)}건")
    c2.metric("처리중", f"{(complaint_df['상태']=='처리중').sum()}건")
    c3.metric("완료", f"{(complaint_df['상태']=='완료').sum()}건")
    c4.metric("고위험", f"{(complaint_df['위험도']=='고').sum()}건", delta="즉시 처리 필요", delta_color="inverse")

    tab1, tab2, tab3 = st.tabs(["📋 민원 목록", "➕ 민원 접수 (입주민 앱)", "📈 처리 통계"])

    with tab1:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            f_status = st.multiselect("상태", complaint_df["상태"].unique(), default=list(complaint_df["상태"].unique()))
        with col_f2:
            f_risk = st.multiselect("위험도", ["고", "중", "저"], default=["고", "중", "저"])
        with col_f3:
            f_type = st.multiselect("유형", complaint_df["유형"].unique(), default=list(complaint_df["유형"].unique()))

        filtered_c = complaint_df[
            complaint_df["상태"].isin(f_status) &
            complaint_df["위험도"].isin(f_risk) &
            complaint_df["유형"].isin(f_type)
        ]

        risk_icon = {"고": "🔴", "중": "🟡", "저": "🟢"}
        disp = filtered_c.copy()
        disp["위험도"] = disp["위험도"].map(lambda r: f"{risk_icon.get(r,'')} {r}")
        st.dataframe(disp[["민원번호", "단지", "세대", "유형", "위험도", "접수일", "상태", "AI점수"]],
                     use_container_width=True, height=400, hide_index=True)

    with tab2:
        st.markdown("**입주민 앱 화면 시뮬레이션 — 비대면 민원 접수**")

        with st.form("complaint_form"):
            col_f, col_d = st.columns(2)
            with col_f:
                new_complex = st.selectbox("단지", COMPLEXES)
                new_unit = st.selectbox("세대", UNITS[:20])
                new_type = st.selectbox("손상 유형", ["누수", "균열", "화재위험", "시설노후", "기타"])
            with col_d:
                new_desc = st.text_area("상세 설명", placeholder="손상 위치, 발생 시점 등을 입력하세요.", height=100)
                new_photo = st.file_uploader("사진 첨부 (앱 카메라)", type=["jpg", "jpeg", "png"])

            submitted = st.form_submit_button("📤 민원 접수", type="primary", use_container_width=True)

        if submitted:
            new_num = f"CM-2026-{1060 + len(st.session_state.get('new_complaints', []))}"
            with st.spinner("AI 자동 분류 및 우선순위 배정 중..."):
                time.sleep(1.2)
            risk_auto = {"누수": "중", "균열": "고", "화재위험": "고", "시설노후": "저", "기타": "저"}[new_type]
            score = round(random.uniform(0.75, 0.97), 2)
            st.success(f"✅ 민원 접수 완료 — **{new_num}**")
            col_r1, col_r2, col_r3 = st.columns(3)
            col_r1.metric("민원번호", new_num)
            col_r2.metric("AI 위험도 판정", risk_auto)
            col_r3.metric("AI 신뢰도", f"{score*100:.0f}%")
            if risk_auto == "고":
                st.error("⚠️ 고위험 민원 — 담당자에게 즉시 알림이 발송되었습니다.")
            else:
                st.info("📬 접수 확인 문자가 발송되었습니다. 처리 현황은 앱에서 확인 가능합니다.")

    with tab3:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("**월별 민원 접수·완료 추이**")
            months = [(datetime.now() - timedelta(days=30 * i)).strftime("%Y-%m") for i in range(5, -1, -1)]
            intake = [random.randint(8, 18) for _ in months]
            done = [random.randint(6, 16) for _ in months]
            fig = go.Figure()
            fig.add_bar(x=months, y=intake, name="접수", marker_color="#3b82f6")
            fig.add_bar(x=months, y=done, name="완료", marker_color="#10b981")
            fig.update_layout(barmode="group", height=300, margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with col_r:
            st.markdown("**처리 기간 분포 (완료 민원)**")
            completed = complaint_df[complaint_df["상태"] == "완료"]["처리일수"].dropna()
            fig2 = px.histogram(completed, nbins=15, labels={"value": "처리 기간 (일)", "count": "건수"},
                                color_discrete_sequence=["#6366f1"], height=300)
            fig2.update_layout(margin=dict(t=10, b=10))
            st.plotly_chart(fig2, use_container_width=True)

# ──────────────────────────────────────────
# PAGE 5: XAI 보고서 생성
# ──────────────────────────────────────────
elif page == "📄 XAI 보고서 생성":
    st.title("📄 XAI 손해사정 자동 보고서")
    st.caption("KICT 가이드라인 기반 — 책임소재 판별 표준 적용, 분쟁 즉시 종결")

    with st.form("report_form"):
        col1, col2 = st.columns(2)
        with col1:
            r_complex = st.selectbox("단지", COMPLEXES)
            r_unit = st.selectbox("세대", UNITS[:20])
            r_type = st.selectbox("사고 유형", ["누수", "균열·구조손상", "화재", "기타"])
        with col2:
            r_date = st.date_input("사고 발생일", value=datetime.now().date())
            r_amount = st.number_input("입주민 청구액 (만원)", min_value=0, value=500, step=50)
            r_xai = st.checkbox("XAI 설명 포함 (판정 근거 상세)", value=True)

        gen_btn = st.form_submit_button("📄 보고서 자동 생성", type="primary", use_container_width=True)

    if gen_btn:
        with st.spinner("AI 손해사정 분석 중 (KICT 기준 적용)..."):
            time.sleep(2.0)

        ai_amount = round(r_amount * random.uniform(0.55, 0.82))
        responsibility = random.choice(["공사 책임 (시설 노후)", "입주민 책임 (부주의)", "공동 책임 (50:50)"])
        confidence = round(random.uniform(0.84, 0.96), 2)

        st.markdown("---")
        st.markdown(f"""
## 📄 AI 손해사정 보고서
> 생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')} | AI모델: Y-MaskNet v2.1 + XAI Engine

| 항목 | 내용 |
|------|------|
| 단지/세대 | {r_complex} / {r_unit} |
| 사고 유형 | {r_type} |
| 사고 발생일 | {r_date} |
| 입주민 청구액 | **{r_amount:,} 만원** |
| **AI 산정 손해액** | **{ai_amount:,} 만원** |
| **책임 소재 판정** | **{responsibility}** |
| AI 신뢰도 | {confidence*100:.0f}% |
| 적용 기준 | KICT 시설물 유지관리 가이드라인 2025 |
        """)

        if r_xai:
            st.markdown("### 🔍 XAI 판정 근거 (설명 가능 AI)")

            factors = {
                "건물 준공 연도 (노후도)": round(random.uniform(0.15, 0.30), 2),
                "최근 점검 이력": round(random.uniform(0.10, 0.25), 2),
                "IoT 센서 이상 감지 횟수": round(random.uniform(0.08, 0.20), 2),
                "AI 균열·손상 탐지 면적": round(random.uniform(0.12, 0.22), 2),
                "입주민 신고 이력": round(random.uniform(0.05, 0.15), 2),
                "동일 유형 사고 빈도": round(random.uniform(0.05, 0.12), 2),
            }
            total = sum(factors.values())
            factors = {k: round(v / total, 2) for k, v in factors.items()}

            fig = px.bar(
                x=list(factors.values()), y=list(factors.keys()),
                orientation="h",
                labels={"x": "기여도 (SHAP value)", "y": ""},
                color=list(factors.values()),
                color_continuous_scale="Blues",
                height=320,
            )
            fig.update_layout(margin=dict(t=10, b=10), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(f"""
**주요 판정 근거:**
- 건물 준공 후 **{random.randint(18,28)}년** 경과 — 노후도 기준치 초과
- 최근 12개월 내 동일 세대 누수 민원 **{random.randint(2,5)}건** 이력
- IoT 습도 센서 **70% 초과** 감지 {random.randint(3,12)}회
- AI 탐지 결과: 손상 면적 **{random.randint(15,80)}cm²**, 신뢰도 {confidence*100:.0f}%

**결론:** {responsibility}로 판정. 입주민 청구액 {r_amount:,}만원 중 AI 산정 **{ai_amount:,}만원** 인정.
처리 예상 기간: **즉시 ~ 2주 이내** (기존 평균 8개월 → 단축)
            """)

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                "⬇️ PDF 보고서 다운로드",
                data=f"AI 손해사정 보고서\n단지: {r_complex}\n손해액: {ai_amount}만원\n책임: {responsibility}".encode("utf-8"),
                file_name=f"XAI_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col_dl2:
            st.button("📤 SH공사 FMS 연동 전송", use_container_width=True,
                      help="실제 운영 시 FMS(시설물정보관리시스템)에 자동 전송됩니다.")

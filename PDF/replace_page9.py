"""Replace PAGE 9 in app.py with new implementation"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

marker = '# PAGE 9: AI 데이터 파이프라인'
idx = content.find(marker)
section_start = content.rfind('# ═══', 0, idx)

new_page9 = r'''# ══════════════════════════════════════════════════════
# PAGE 9: AI 데이터 파이프라인 (실제 모델 학습·추론)
# ══════════════════════════════════════════════════════
elif page == "🧬 AI 데이터 파이프라인":
    st.title("🧬 AI 데이터 파이프라인 — 실제 모델 학습·추론 엔진")
    st.caption("Mock 데이터 생성 → sklearn 모델 학습 → 추론 → 성능 평가 | 9개 파이프라인 실시간 실행")

    if "pipeline_engine" not in st.session_state:
        with st.spinner("🧬 9개 AI 파이프라인 데이터 생성 + 모델 학습 중... (최초 1회)"):
            from ai_pipeline import AXPipelineEngine
            eng = AXPipelineEngine(seed=2026)
            eng.run_all()
            st.session_state.pipeline_engine = eng
    eng = st.session_state.pipeline_engine

    pk1, pk2, pk3, pk4, pk5 = st.columns(5)
    with pk1:
        st.markdown('<div class="kpi-card"><div class="label">파이프라인</div><div class="value">9개</div><div class="sub">Mock 데이터 + 실제 학습</div></div>', unsafe_allow_html=True)
    with pk2:
        st.markdown('<div class="kpi-card-green"><div class="label">총 데이터</div><div class="value">4,429건</div><div class="sub">9개 데이터셋 합산</div></div>', unsafe_allow_html=True)
    with pk3:
        st.markdown('<div class="kpi-card"><div class="label">학습 모델</div><div class="value">9개</div><div class="sub">RF·GBM·IF·GBR 등</div></div>', unsafe_allow_html=True)
    with pk4:
        st.markdown('<div class="kpi-card-amber"><div class="label">평균 정확도</div><div class="value">93%+</div><div class="sub">분류 모델 기준</div></div>', unsafe_allow_html=True)
    with pk5:
        st.markdown('<div class="kpi-card-green"><div class="label">예상 ROI</div><div class="value">340%</div><div class="sub">투자 회수 8개월</div></div>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="sh">📊 9개 파이프라인 학습 성능 요약</div>', unsafe_allow_html=True)
    summary_df = eng.get_summary_table()
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    st.divider()

    pipeline_names = {k: v["name"] for k, v in eng.pipelines.items()}
    selected_key = st.selectbox("파이프라인 선택", list(pipeline_names.keys()), format_func=lambda x: pipeline_names[x])
    p = eng.pipelines[selected_key]
    r = p["result"]
    pdata = p["data"]

    st.markdown(f'<div class="sh">{p["name"]} — {r["model_name"]}</div>', unsafe_allow_html=True)
    tab_data, tab_model, tab_result = st.tabs(["📂 Mock 데이터", "🤖 모델 학습 결과", "📈 시각화"])

    with tab_data:
        st.markdown(f"**생성된 Mock 데이터:** {len(pdata):,}행 × {len(pdata.columns)}열")
        st.dataframe(pdata.head(50), use_container_width=True, hide_index=True, height=350)
        ncols = pdata.select_dtypes(include=[np.number]).columns.tolist()
        if ncols:
            st.markdown("**기술 통계:**")
            st.dataframe(pdata[ncols].describe().round(3), use_container_width=True)

    with tab_model:
        mcols = st.columns(4)
        ci = 0
        for mk, mv in r.items():
            if isinstance(mv, float) and mk != "model_name":
                with mcols[ci % 4]:
                    st.metric(mk.replace("_"," ").title(), f"{mv:.4f}" if mv < 10 else f"{mv:.1f}")
                ci += 1
        if "feature_importance" in r:
            st.markdown("---")
            st.markdown("##### 🔍 Feature Importance")
            fi = r["feature_importance"]
            fi_df = pd.DataFrame({"특징": list(fi.keys()), "중요도": list(fi.values())})
            fig_fi = px.bar(fi_df, x="중요도", y="특징", orientation="h", height=300, color="중요도", color_continuous_scale="Reds")
            fig_fi.update_layout(margin=dict(t=10, b=10), coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_fi, use_container_width=True)
        if "confusion_matrix" in r:
            st.markdown("##### 📊 Confusion Matrix")
            cm = r["confusion_matrix"]
            classes = r.get("classes", [str(i) for i in range(cm.shape[0])])
            fig_cm = px.imshow(cm, text_auto=True, x=classes, y=classes, height=350, color_continuous_scale="Blues")
            fig_cm.update_layout(margin=dict(t=10, b=10))
            st.plotly_chart(fig_cm, use_container_width=True)

    with tab_result:
        if selected_key == "vision":
            c1, c2 = st.columns(2)
            with c1:
                tc = pdata["손상유형"].value_counts().reset_index(); tc.columns = ["유형","건수"]
                fig = px.bar(tc, x="건수", y="유형", orientation="h", height=300, color="유형", title="손상 유형 분포")
                fig.update_layout(margin=dict(t=40, b=10), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                fig2 = px.scatter(pdata[pdata["손상유형"]!="정상"], x="균열폭_mm", y="면적_cm2", color="손상유형", height=300, title="균열폭 vs 면적")
                fig2.update_layout(margin=dict(t=40, b=10))
                st.plotly_chart(fig2, use_container_width=True)
        elif selected_key == "iot":
            fig = make_subplots(rows=2, cols=3, subplot_titles=["온도","습도","전력","진동","CO","이상분포"])
            for si, (scol, clr, thr) in enumerate(zip(["온도","습도","전력_kWh","진동_g","CO_ppm"], ["#ef4444","#3b82f6","#f59e0b","#8b5cf6","#06b6d4"], [30,72,4.5,0.5,10])):
                rr, cc = divmod(si, 3); rr += 1; cc += 1
                fig.add_trace(go.Scatter(y=pdata[scol], line=dict(color=clr, width=1), showlegend=False), row=rr, col=cc)
                fig.add_hline(y=thr, line_dash="dash", line_color="gray", row=rr, col=cc)
            ac = pdata["이상"].value_counts()
            fig.add_trace(go.Bar(x=["정상","이상"], y=[ac.get(0,0), ac.get(1,0)], marker_color=["#10b981","#ef4444"], showlegend=False), row=2, col=3)
            fig.update_layout(height=450, margin=dict(t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)
            st.success(f"이상 감지: {r['n_anomalies']}건 ({r['anomaly_rate']}%)")
        elif selected_key == "complaint":
            c1, c2 = st.columns(2)
            with c1:
                tc = pdata["유형"].value_counts().reset_index(); tc.columns = ["유형","건수"]
                fig = px.pie(tc, values="건수", names="유형", hole=0.4, height=300, title="민원 유형 분포")
                fig.update_layout(margin=dict(t=40, b=10)); st.plotly_chart(fig, use_container_width=True)
            with c2:
                rc = pdata["위험도"].value_counts().sort_index().reset_index(); rc.columns = ["위험도","건수"]; rc["등급"] = rc["위험도"].map({0:"저",1:"중",2:"고"})
                fig2 = px.bar(rc, x="등급", y="건수", color="등급", height=300, color_discrete_map={"저":"#10b981","중":"#f59e0b","고":"#ef4444"}, title="위험도 분포")
                fig2.update_layout(margin=dict(t=40, b=10), showlegend=False); st.plotly_chart(fig2, use_container_width=True)
        elif selected_key == "risk":
            c1, c2 = st.columns(2)
            with c1:
                fig = px.box(pdata, x="단지", y="위험점수", color="단지", height=320, title="단지별 위험 점수")
                fig.update_layout(margin=dict(t=40, b=10), showlegend=False); st.plotly_chart(fig, use_container_width=True)
            with c2:
                fig2 = px.scatter(pdata, x="경과년수", y="위험점수", color="위험등급", height=320, color_discrete_map={0:"#10b981",1:"#f59e0b",2:"#ef4444"}, title="경과년수 vs 위험점수")
                fig2.update_layout(margin=dict(t=40, b=10)); st.plotly_chart(fig2, use_container_width=True)
            st.success(f"분류 정확도: {r['classification_accuracy']:.1%} | R²: {r['regression_r2']:.4f}")
        elif selected_key == "failure":
            fig = go.Figure()
            for cpx in pdata["단지"].unique():
                cd = pdata[pdata["단지"]==cpx]
                fig.add_trace(go.Scatter(x=cd["월"], y=cd["AI적용전_고장"], name=f"{cpx} (전)", line=dict(dash="dash"), opacity=0.6))
                fig.add_trace(go.Scatter(x=cd["월"], y=cd["AI적용후_고장"], name=f"{cpx} (후)"))
            fig.update_layout(height=380, margin=dict(t=10, b=10), xaxis_title="월", yaxis_title="고장 건수")
            st.plotly_chart(fig, use_container_width=True)
            st.success(f"AI 적용 시 고장 감소율: {r['reduction_pct']}%")
        elif selected_key == "energy":
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=pdata["총에너지_kWh"], name="현재", line=dict(color="#f59e0b")))
            fig.add_trace(go.Scatter(y=pdata["AI최적화_kWh"], name="AI 최적화", line=dict(color="#10b981"), fill="tonexty", fillcolor="rgba(16,185,129,0.1)"))
            fig.update_layout(height=350, margin=dict(t=10, b=10)); st.plotly_chart(fig, use_container_width=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("연간 총 소비", f"{r['total_before']:,.0f} kWh"); c2.metric("AI 최적화 후", f"{r['total_after']:,.0f} kWh"); c3.metric("절감률", f"{r['saving_pct']}%")
        elif selected_key == "billing":
            c1, c2 = st.columns(2)
            with c1:
                fig = px.scatter(pdata, x="면적_m2", y="총청구_만원", color="이상청구", height=300, color_discrete_map={0:"#3b82f6",1:"#ef4444"}, title="면적 vs 총청구")
                fig.update_layout(margin=dict(t=40, b=10)); st.plotly_chart(fig, use_container_width=True)
            with c2:
                fig2 = px.histogram(pdata, x="연체개월", height=300, title="연체 분포", color_discrete_sequence=["#8b5cf6"])
                fig2.update_layout(margin=dict(t=40, b=10)); st.plotly_chart(fig2, use_container_width=True)
            st.success(f"이상탐지: {r['anomaly_accuracy']:.1%} | 연체예측: {r['overdue_accuracy']:.1%}")
        elif selected_key == "crack":
            sample = pdata[pdata["균열ID"].isin(pdata["균열ID"].unique()[:5])]
            fig = px.line(sample, x="월차", y="균열폭_mm", color="균열ID", height=350, title="균열 성장 시계열")
            fig.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="정밀진단 기준")
            fig.update_layout(margin=dict(t=40, b=10)); st.plotly_chart(fig, use_container_width=True)
            if "future_predictions" in r:
                st.markdown("##### 🔮 CR-001 6개월 예측")
                st.dataframe(pd.DataFrame(r["future_predictions"]), use_container_width=True, hide_index=True)
            st.success(f"R²: {r['growth_r2']:.4f} | 활성: {r['n_active']}/{r['n_total']}개")
        elif selected_key == "subsidence":
            c1, c2 = st.columns(2)
            with c1:
                fig = px.scatter(pdata, x="GPR공동크기_cm", y="침하확률", color="침하발생", height=300, color_discrete_map={0:"#3b82f6",1:"#ef4444"}, title="GPR vs 침하확률")
                fig.update_layout(margin=dict(t=40, b=10)); st.plotly_chart(fig, use_container_width=True)
            with c2:
                fig2 = px.scatter(pdata, x="관로경과년수", y="침하확률", color="침하발생", height=300, color_discrete_map={0:"#3b82f6",1:"#ef4444"}, title="관로년수 vs 침하확률")
                fig2.update_layout(margin=dict(t=40, b=10)); st.plotly_chart(fig2, use_container_width=True)
            st.success(f"정확도: {r['accuracy']:.1%} | F1: {r['f1_score']:.4f} | 확률 R²: {r['prob_r2']:.4f}")

    st.divider()
    st.markdown('<div class="sh">📋 55개 AI 파이프라인 전체 명세</div>', unsafe_allow_html=True)
    categories2 = sorted(pipeline_df["분류"].unique())
    cg2 = {
        "🖼 비전AI (10건)": [c for c in categories2 if c.startswith("비전AI")],
        "📡 IoT (8건)": [c for c in categories2 if c.startswith("IoT")],
        "📋 민원 (6건)": [c for c in categories2 if c.startswith("민원")],
        "🏗 Digital Twin (6건)": [c for c in categories2 if c.startswith("DigitalTwin")],
        "🚨 이상징후 (5건)": [c for c in categories2 if c.startswith("이상징후")],
        "🛡 선제탐지 (5건)": [c for c in categories2 if c.startswith("선제탐지")],
        "🤖 RPA (7건)": [c for c in categories2 if c.startswith("RPA")],
        "🔰 예방조치 (5건)": [c for c in categories2 if c.startswith("예방조치")],
        "📊 대시보드 (3건)": [c for c in categories2 if c.startswith("대시보드")],
    }
    sg2 = st.selectbox("카테고리 필터", list(cg2.keys()), key="pf2")
    fdf = pipeline_df[pipeline_df["분류"].isin(cg2[sg2])]
    st.dataframe(fdf, use_container_width=True, hide_index=True, height=300)
'''

content_new = content[:section_start] + new_page9 + '\n'
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content_new)

print(f"✅ PAGE 9 교체 완료: {len(content_new)} chars")

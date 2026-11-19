"""
10번 페이지 — 모델 성능 · 검증 · Page 10 — model performance & validation (v2.5)
데이터: ai_validation.ValidationSuite.run_all() 결과 (합성 데이터, seed 2026)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import ui_common as ui
from ui_common import T

FEAT_EN = {
    "경과년수": "Building age (yr)", "IoT이상횟수": "IoT anomaly count", "균열성장률_mm월": "Crack growth (mm/mo)",
    "점검경과일수": "Days since inspection", "기상위험지수": "Weather risk index",
    "드라이비트면적_cm": "Dryvit area (cm)", "민원빈도": "Complaint frequency",
}
TYPE_EN = {"누수": "Leak", "균열·구조손상": "Crack / structural", "화재·가연성외벽": "Fire / combustible façade",
           "시설노후": "Ageing facility", "관리비이의": "Fee dispute", "계약관련": "Contract", "기타": "Other"}
CPX_EN = {"강남A동": "Gangnam A", "마포B동": "Mapo B", "서초E동": "Seocho E", "노원C동": "Nowon C",
          "강서D동": "Gangseo D", "구미A동": "Gumi A", "안동B동": "Andong B"}

GLOSSARY = [
    ("Stratified 5-fold", "데이터를 5 조각으로 나누되 각 조각의 클래스 비율을 같게 한다. 4 조각으로 학습, 1 조각으로 평가를 5번 돈다.",
     "Split data into 5 parts with equal class ratios; train on 4, test on 1, five times."),
    ("Nested CV", "바깥 CV 로 성능을 재고, 안쪽 CV 로 하이퍼파라미터를 고른다. 튜닝이 평가 데이터를 보지 않는다.",
     "Outer CV measures score; inner CV picks hyper-parameters, so tuning never sees test folds."),
    ("Walk-forward", "과거 구간으로 학습하고 바로 다음 구간으로 평가한 뒤 앞으로 이동한다.",
     "Train on the past, test on the next block, then roll forward."),
    ("HGB", "HistGradientBoosting. 값을 구간(histogram)으로 묶어 빠르게 학습하는 gradient boosting.",
     "HistGradientBoosting: gradient boosting on binned (histogram) features."),
    ("F1 (macro)", "클래스마다 F1 을 구해 단순 평균. 적은 클래스도 같은 무게로 본다.",
     "Mean of per-class F1, so rare classes weigh the same."),
    ("R²", "결정계수. 1 이면 완벽, 0 이면 평균으로 찍은 것과 같다.",
     "Coefficient of determination: 1 = perfect, 0 = same as predicting the mean."),
    ("WAPE", "Weighted Absolute Percentage Error. Σ|실제−예측| ÷ Σ|실제|. 0 이 많은 건수 데이터용.",
     "Weighted Absolute Percentage Error: Σ|actual−pred| ÷ Σ|actual|, robust to zeros."),
    ("Naive", "전월(전일) 값을 그대로 다음 예측으로 쓰는 기준선.", "Baseline that repeats last month's (day's) value."),
    ("PR-AUC", "Precision–Recall 곡선 아래 면적. 이상이 드문 데이터에서 accuracy 대신 쓴다. 무작위면 이상 비율과 같다.",
     "Area under the precision–recall curve; for rare anomalies. Random = base rate."),
    ("F1@k", "점수 상위 k 개(k = 실제 이상 수)를 이상으로 볼 때의 F1.", "F1 when the top-k scores (k = true anomaly count) are flagged."),
    ("Brier score", "예측 확률과 실제(0/1)의 제곱 오차 평균. 작을수록 좋다.", "Mean squared error between predicted probability and outcome (0/1); lower is better."),
    ("Calibration", "예측 확률이 실제 빈도와 맞도록 보정. 여기서는 sigmoid(Platt) 방식.", "Adjusting probabilities to match observed frequency; sigmoid (Platt) here."),
    ("Permutation importance", "한 feature 값을 섞었을 때 R² 가 얼마나 떨어지는지로 잰 중요도.", "Importance = drop in R² when one feature is shuffled."),
    ("Occlusion 기여도", "한 feature 만 학습 중앙값으로 바꿨을 때 예측 점수가 변한 양.", "Change in predicted score when one feature is set to its training median."),
    ("TF-IDF (char n-gram)", "글자 2~4 개 묶음의 빈도에 희귀도 가중치를 곱한 문장 벡터. 형태소 분석기 없이 한국어를 다룬다.",
     "Sentence vector from 2–4 character chunks weighted by rarity; handles Korean without a tokenizer."),
    ("Logistic Regression", "확률을 내는 선형 분류기.", "Linear classifier that outputs probabilities."),
]


def _f(v, d=3):
    return f"{v:.{d}f}"


def render():
    st.title(T("📐 모델 성능 · 검증", "📐 Model performance · validation"))
    st.caption(T("v2.5 · 합성 데이터(seed 2026) 기준 · 실데이터 성능이 아니다",
                 "v2.5 · synthetic data (seed 2026) · not real-world performance"))

    c1, c2 = st.columns(2)
    c1.markdown(T(
        "**배경 · 현황** — v2.2 의 9개 파이프라인은 무작위 train/test 를 한 번만 나눠 점수를 냈다. 시계열은 미래 값이 학습에 섞였다.",
        "**Background** — v2.2 scored its 9 pipelines on one random train/test split. Time series leaked future values into training."))
    c2.markdown(T(
        "**왜 하는가** — 점수가 우연인지, 튜닝·feature 개선이 진짜 효과인지 가려 수요처 보고에 쓸 수 있는 수치를 만든다.",
        "**Why** — to tell luck from real gains of tuning and features, producing numbers fit for demand-site reports."))

    with st.spinner(T("검증 실행 중... (서버당 최초 1회, 약 1분)", "Running validation... (once per server, ~1 min)")):
        out = ui.get_validation()

    with st.expander(T("용어 정리 표", "Glossary"), expanded=False):
        st.dataframe(pd.DataFrame([{T("용어", "Term"): g[0], T("정의", "Definition"): T(g[1], g[2])} for g in GLOSSARY]),
                     hide_index=True, use_container_width=True)

    with st.expander(T("설정 · 누가 · 언제 · 왜", "Settings · who · when · why"), expanded=False):
        st.dataframe(pd.DataFrame([
            {T("항목", "Item"): "seed", T("값", "Value"): "2026", T("근거", "Reason"):
             T("v2.2 부터 굳은 기본값. 재현용.", "Default fixed since v2.2, for reproducibility.")},
            {T("항목", "Item"): T("분류 CV", "Classification CV"), T("값", "Value"): "outer 5 × inner 3",
             T("근거", "Reason"): T("v2.5(2026-11-19) 에서 정함. 300~500 행이라 5-fold 가 fold 당 60~100 행을 남긴다.",
                                   "Set in v2.5 (2026-11-19). With 300–500 rows, 5-fold leaves 60–100 test rows.")},
            {T("항목", "Item"): T("HGB 탐색 범위", "HGB grid"), T("값", "Value"): "max_depth ∈ {3, None}, lr 0.1, 100 iter",
             T("근거", "Reason"): T("Render 1 vCPU 에서 1분 안에 끝나도록 줄였다.", "Kept small to finish within ~1 min on Render's 1 vCPU.")},
            {T("항목", "Item"): T("시계열 분할", "Time-series split"), T("값", "Value"):
             T("고장: 6개월 블록 4개 · 에너지: 40일 × 5 · 균열: 6~11개월 1개월씩",
               "Failure: four 6-month blocks · Energy: 5 × 40 days · Crack: months 6–11 one by one"),
             T("근거", "Reason"): T("각 데이터 길이(36개월 · 365일 · 12개월)에 맞춰 v2.5 에서 정함.",
                                   "Chosen in v2.5 to fit each length (36 mo, 365 d, 12 mo).")},
            {T("항목", "Item"): T("확률 보정", "Calibration"), T("값", "Value"): "sigmoid, cv=5",
             T("근거", "Reason"): T("400 행은 isotonic 에 작다.", "400 rows is small for isotonic.")},
            {T("항목", "Item"): T("민원 문장", "Complaint text"), T("값", "Value"):
             T("700 문장 · 부차 민원 30 % · 라벨 오류 5 %", "700 sentences · 30 % secondary issue · 5 % label error"),
             T("근거", "Reason"): T("쉬운 문장만 있으면 F1 = 1.0 이 나와 의미가 없었다 (v2.5 첫 실행).",
                                   "Clean templates gave F1 = 1.0, which says nothing (first v2.5 run).")},
        ]), hide_index=True, use_container_width=True)

    tabs = st.tabs([T("① 분류", "① Classification"), T("② 시계열", "② Time series"), T("③ 이상 탐지", "③ Anomaly"),
                    T("④ 확률 보정", "④ Calibration"), T("⑤ XAI", "⑤ XAI"), T("⑥ 민원 문장", "⑥ Complaint text"),
                    T("한계 · 다시 돌리기", "Limits · rerun")])

    # ① 분류
    with tabs[0]:
        df = out["classification"]
        st.markdown(T("**질문** — 튜닝한 HGB 가 기존 모형보다 F1 이 높은가? 그 차이가 fold 간 흔들림보다 큰가?",
                      "**Question** — does tuned HGB beat the original model on F1, by more than fold-to-fold noise?"))
        show = pd.DataFrame({
            T("과제", "Task"): df["task"].str.split(" · ").str[0 if ui.lang() == "ko" else -1],
            T("행 수", "Rows"): df["n"],
            T("최빈 클래스 비율", "Majority share"): df["majority_acc"].map(_f),
            T("기존 모형", "Original model"): df["base_model"],
            T("기존 F1", "Original F1"): df.apply(lambda r: f"{r.base_f1:.3f} ± {r.base_f1_sd:.3f}", axis=1),
            T("HGB F1", "HGB F1"): df.apply(lambda r: f"{r.tuned_f1:.3f} ± {r.tuned_f1_sd:.3f}", axis=1),
            "ΔF1": df["delta_f1"].map(lambda v: f"{v:+.3f}"),
            T("고른 설정", "Chosen params"): df["best_params"],
        })
        st.dataframe(show, hide_index=True, use_container_width=True)
        fig = go.Figure()
        lab = show[T("과제", "Task")]
        fig.add_bar(name=T("기존 모형", "Original"), x=lab, y=df["base_f1"], error_y=dict(array=df["base_f1_sd"]), marker_color="#94a3b8")
        fig.add_bar(name=T("튜닝 HGB", "Tuned HGB"), x=lab, y=df["tuned_f1"], error_y=dict(array=df["tuned_f1_sd"]), marker_color="#2563eb")
        fig.update_layout(barmode="group", height=320, margin=dict(t=20), legend=dict(orientation="h", y=1.12))
        ui.axes(fig, x=("과제", "Task"), y=("F1 macro (0~1, 5-fold 평균 ± 표준편차)", "F1 macro (0–1, 5-fold mean ± SD)"))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(T(
            "**읽은 것** — 위험 등급은 F1 이 0.60 → 0.75 로 올랐다. 그러나 fold 간 표준편차가 0.2 안팎이라 확실한 개선은 아니다. "
            "고위험 행이 300 행 중 7 % 뿐이기 때문이다. 비전 손상은 0.50 → 0.53 에 그쳤다. 합성 데이터에서 수직균열과 수평균열이 같은 방식으로 생성돼 feature 로 구분되지 않는다. "
            "그래서 비전은 모형이 아니라 실제 이미지 feature 가 필요하다.",
            "**Reading** — Risk grade F1 rose 0.60 → 0.75, but fold SD is about 0.2, so the gain is not certain: high-risk rows are only 7 % of 300. "
            "Vision damage moved only 0.50 → 0.53: vertical and horizontal cracks are generated identically, so the features cannot separate them. "
            "Vision therefore needs real image features, not a different model."))
        key = st.selectbox(T("혼동행렬 과제", "Confusion matrix for"), df["key"].tolist(), key="p10_cm",
                           format_func=lambda k: lab[df["key"].tolist().index(k)])
        cm = out["confusion"][key]
        names = [TYPE_EN.get(c, c) if ui.lang() == "en" else c for c in cm["classes"]]
        fcm = px.imshow(cm["cm"], x=names, y=names, text_auto=True, color_continuous_scale="Blues", height=380)
        ui.axes(fcm, x=("모형이 예측한 클래스", "Predicted class"), y=("실제 클래스", "Actual class"))
        st.plotly_chart(fcm, use_container_width=True)
        st.caption(T("튜닝 HGB 의 out-of-fold 예측 (각 행은 학습에 쓰이지 않은 fold 에서 예측).",
                     "Out-of-fold predictions of tuned HGB (each row predicted by a model that never saw it)."))

    # ② 시계열
    with tabs[1]:
        ts = out["timeseries"]
        st.markdown(T("**질문** — 무작위 분할 R² 는 미래 정보가 섞여 부풀려졌는가? 구조를 반영한 모형이 전월값(naive)을 이기는가?",
                      "**Question** — is random-split R² inflated by future leakage? Does a structure-aware model beat the naive last value?"))
        tt = pd.DataFrame({
            T("과제", "Task"): ts["task"].str.split(" · ").str[0 if ui.lang() == "ko" else -1],
            T("무작위 R²", "Random R²"): ts["random_r2"].map(_f),
            T("WF 기존 R²", "WF original R²"): ts["wf_base_r2"].map(_f),
            T("WF 개선 R²", "WF improved R²"): ts["wf_imp_r2"].map(_f),
            T("기존 WAPE", "Original WAPE"): ts["wf_base_wape"].map(_f),
            T("개선 WAPE", "Improved WAPE"): ts["wf_imp_wape"].map(_f),
            T("Naive WAPE", "Naive WAPE"): ts["naive_wape"].map(_f),
            T("바꾼 것", "Change"): ts["change"].map(lambda c: c.split(" · ")[0 if ui.lang() == "ko" else -1]),
        })
        st.dataframe(tt, hide_index=True, use_container_width=True)
        fig = go.Figure()
        lab = tt[T("과제", "Task")]
        fig.add_bar(name=T("기존 모형", "Original"), x=lab, y=ts["wf_base_wape"], marker_color="#94a3b8")
        fig.add_bar(name=T("전월값 naive", "Naive last value"), x=lab, y=ts["naive_wape"], marker_color="#f59e0b")
        fig.add_bar(name=T("개선 모형", "Improved"), x=lab, y=ts["wf_imp_wape"], marker_color="#2563eb")
        fig.update_layout(barmode="group", height=320, margin=dict(t=20), legend=dict(orientation="h", y=1.12))
        ui.axes(fig, x=("과제", "Task"), y=("walk-forward 오차 WAPE (낮을수록 좋음)", "Walk-forward error WAPE (lower is better)"))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(T(
            "**읽은 것** — 고장 예측의 무작위 R² 는 0.84 였지만 walk-forward 로는 0.34 였다. 무작위 분할이 미래 달을 학습에 넣었기 때문이다. "
            "나무 모형은 추세를 외삽하지 못한다. 추세 + 단지별 계절 진폭 선형 모형으로 바꾸자 WAPE 가 0.17 → 0.09 로 줄어 naive(0.12)를 이겼다. "
            "균열은 폭 대신 증가량을 예측해 WAPE 0.12 → 0.02 가 됐다.",
            "**Reading** — Failure random-split R² was 0.84 but only 0.34 walk-forward: the random split put future months into training. "
            "Trees cannot extrapolate a trend. A linear trend + per-complex seasonal model cut WAPE 0.17 → 0.09, beating naive (0.12). "
            "For cracks, predicting the increment instead of the width cut WAPE 0.12 → 0.02."))
        key = st.selectbox(T("예측 곡선 과제", "Forecast curve for"), ts["key"].tolist(), key="p10_ts",
                           format_func=lambda k: lab[ts["key"].tolist().index(k)])
        cv = out["ts_curves"][key]
        cdf = pd.DataFrame({"x": cv["x"], "y": cv["y"], "b": cv["p_base"], "i": cv["p_imp"]}).groupby("x").sum().reset_index()
        f2 = go.Figure()
        f2.add_scatter(x=cdf["x"], y=cdf["y"], name=T("실제", "Actual"), mode="lines+markers", line=dict(color="#0f172a"))
        f2.add_scatter(x=cdf["x"], y=cdf["b"], name=T("기존 모형", "Original"), mode="lines", line=dict(color="#94a3b8", dash="dot"))
        f2.add_scatter(x=cdf["x"], y=cdf["i"], name=T("개선 모형", "Improved"), mode="lines", line=dict(color="#2563eb"))
        xl = {"failure": ("개월 (0 = 첫 달)", "Month (0 = first)"), "energy": ("날짜 (1년 중 몇째 날)", "Day of year"),
              "crack": ("관측 개월 (개월)", "Months observed")}[key]
        yl = {"failure": ("4개 단지 합계 고장 건수 (건)", "Failures, sum of 4 complexes (cases)"),
              "energy": ("하루 전력 사용량 (kWh)", "Daily energy use (kWh)"),
              "crack": ("50개 균열 폭 합계 (mm)", "Sum of 50 crack widths (mm)")}[key]
        ui.axes(f2, x=xl, y=yl)
        f2.update_layout(height=340, margin=dict(t=20), legend=dict(orientation="h", y=1.12))
        st.plotly_chart(f2, use_container_width=True)

    # ③ 이상 탐지
    with tabs[2]:
        an = out["anomaly"]
        st.markdown(T("**질문** — accuracy 가 높아 보이는 것은 이상이 드물어서인가? 실제로 이상을 얼마나 잘 골라내는가?",
                      "**Question** — is high accuracy just rarity? How well are anomalies actually ranked?"))
        st.dataframe(pd.DataFrame({
            T("과제", "Task"): an["task"].str.split(" · ").str[0 if ui.lang() == "ko" else -1],
            T("방법", "Method"): an["method"],
            T("이상 비율", "Base rate"): an["base_rate"].map(lambda v: f"{v:.1%}"),
            T("전부 정상이라 찍을 때 accuracy", "Accuracy of 'all normal'"): an["acc_all_normal"].map(lambda v: f"{v:.1%}"),
            "PR-AUC": an["pr_auc"].map(_f), "F1@k": an["f1_at_k"].map(_f),
        }), hide_index=True, use_container_width=True)
        st.markdown(T(
            "**읽은 것** — 관리비는 '전부 정상'이라고만 해도 accuracy 95.2 % 다. 그래서 v2.2 의 99.5 % 는 거의 정보가 없다. "
            "면적당 관리비 · 1인당 전기·수도 비율 feature 를 넣으니 비지도 IsolationForest PR-AUC 가 0.953 → 0.976 으로 올랐다. "
            "IoT 는 단순 |z| 규칙(0.79)이 IsolationForest(0.66)보다 좋았다. IoT 라벨이 센서 임계값으로 만들어졌기 때문이다.",
            "**Reading** — For billing, predicting 'all normal' already scores 95.2 % accuracy, so v2.2's 99.5 % carries little information. "
            "Adding per-m² fee and per-person power/water ratios lifted unsupervised IsolationForest PR-AUC 0.953 → 0.976. "
            "For IoT, a plain |z| rule (0.79) beat IsolationForest (0.66), because IoT labels were generated from sensor thresholds."))

    # ④ 확률 보정
    with tabs[3]:
        c = out["calibration"]
        st.markdown(T("**질문** — 지반침하 확률 0.7 이라고 하면 실제로 10번 중 7번 꺼지는가?",
                      "**Question** — when the model says 0.7 subsidence probability, does it happen 7 times in 10?"))
        k1, k2, k3 = st.columns(3)
        ui.kpi(k1, "kpi-card", T("보정 전 Brier", "Brier, raw"), _f(c["brier_raw"]), T("낮을수록 좋음", "lower is better"))
        ui.kpi(k2, "kpi-card-green", T("보정 후 Brier", "Brier, calibrated"), _f(c["brier_cal"]), "sigmoid, cv=5")
        ui.kpi(k3, "kpi-card-amber", T("평균 확률만 쓸 때", "Base-rate only"), _f(c["brier_climatology"]),
               T(f"발생률 {c['base_rate']:.1%}", f"base rate {c['base_rate']:.1%}"))
        fig = go.Figure()
        fig.add_scatter(x=[0, 1], y=[0, 1], mode="lines", name=T("완벽한 보정", "Perfect calibration"), line=dict(color="#cbd5e1", dash="dash"))
        for nm, col, lb in (("raw", "#94a3b8", T("보정 전", "Raw")), ("cal", "#2563eb", T("보정 후", "Calibrated"))):
            mp, fr = c["curves"][nm]
            fig.add_scatter(x=mp, y=fr, mode="lines+markers", name=lb, line=dict(color=col))
        ui.axes(fig, x=("모형이 말한 침하 확률 (0~1)", "Predicted subsidence probability (0–1)"),
                y=("실제로 꺼진 비율 (0~1)", "Observed subsidence share (0–1)"))
        fig.update_layout(height=360, margin=dict(t=20), legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(T(
            "**읽은 것** — 보정 전 Brier 0.236 은 평균 확률만 쓴 0.238 과 거의 같았다. 확률 값 자체는 쓸모가 적었다는 뜻이다. "
            "sigmoid 보정 후 0.193 으로 줄었다. 그래서 점검 우선순위에는 보정된 확률을 쓴다.",
            "**Reading** — Raw Brier 0.236 was almost the base-rate-only 0.238, so raw probabilities carried little value. "
            "Sigmoid calibration cut it to 0.193, so inspection priority should use calibrated probabilities."))

    # ⑤ XAI
    with tabs[4]:
        x = out["xai"]
        fe = (lambda f: FEAT_EN.get(f, f)) if ui.lang() == "en" else (lambda f: f)
        st.markdown(T("**질문** — 모형이 말하는 위험 근거가 실제 위험 생성식과 맞는가?",
                      "**Question** — do the model's risk reasons match the true risk formula?"))
        p = x["perm"].iloc[::-1]
        fig = go.Figure(go.Bar(x=p["mean"], y=p["feature"].map(fe), orientation="h",
                               error_x=dict(array=p["std"]), marker_color="#2563eb"))
        ui.axes(fig, x=("섞었을 때 R² 하락 (클수록 중요)", "Drop in R² when shuffled (larger = more important)"),
                y=("위험 지표", "Risk indicator"))
        fig.update_layout(height=320, margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)
        cpx = st.selectbox(T("단지", "Complex"), sorted(x["local"]["단지"].unique()), key="p10_xai",
                           format_func=lambda v: CPX_EN.get(v, v) if ui.lang() == "en" else v)
        loc = x["local"][x["local"]["단지"] == cpx].sort_values("model")
        f2 = go.Figure()
        f2.add_bar(y=loc["feature"].map(fe), x=loc["model"], orientation="h", name=T("모형 기여도", "Model contribution"), marker_color="#2563eb")
        f2.add_bar(y=loc["feature"].map(fe), x=loc["true"], orientation="h", name=T("생성식 참값", "True (formula)"), marker_color="#f59e0b")
        ui.axes(f2, x=("위험 점수에 더한 양 (점, 중앙값 대비)", "Points added to risk score (vs median)"), y=("위험 지표", "Risk indicator"))
        f2.update_layout(barmode="group", height=360, margin=dict(t=20), legend=dict(orientation="h", y=1.12))
        st.plotly_chart(f2, use_container_width=True)
        st.markdown(T(
            f"**읽은 것** — 모형 R² {x['test_r2']:.2f}. 모든 단지 × 지표에서 모형 기여도와 참값의 상관은 {x['corr_true']:.2f} 였다. "
            "IoT 이상 횟수가 가장 중요했고 이는 생성식의 가중치(건당 5점)와 맞다. 기존 화면의 'SHAP' 막대는 고정 범위 값이었다. 이 탭의 값은 모형에서 계산한 것이다.",
            f"**Reading** — Model R² {x['test_r2']:.2f}. Across all complex × indicator pairs, model vs true contribution correlation is {x['corr_true']:.2f}. "
            "IoT anomaly count matters most, matching the formula weight (5 points each). The older 'SHAP' bars used fixed ranges; values here are computed from the model."))

    # ⑥ 민원 문장
    with tabs[5]:
        t = out["text"]
        st.markdown(T("**질문** — 형태소 분석기 없이 글자 n-gram 만으로 민원 7종을 나눌 수 있는가?",
                      "**Question** — can character n-grams alone sort complaints into 7 types without a Korean tokenizer?"))
        k1, k2, k3 = st.columns(3)
        ui.kpi(k1, "kpi-card", "F1 macro", f"{t['f1'][0]:.3f}", f"± {t['f1'][1]:.3f} (5-fold)")
        ui.kpi(k2, "kpi-card-green", "Accuracy", f"{t['acc'][0]:.3f}", f"± {t['acc'][1]:.3f}")
        ui.kpi(k3, "kpi-card-amber", T("문장 수", "Sentences"), f"{len(t['data'])}", T("라벨 오류 5 % 포함", "incl. 5 % label error"))
        names = [TYPE_EN.get(c, c) if ui.lang() == "en" else c for c in t["classes"]]
        fcm = px.imshow(t["cm"], x=names, y=names, text_auto=True, color_continuous_scale="Blues", height=380)
        ui.axes(fcm, x=("모형이 예측한 유형", "Predicted type"), y=("접수된 유형", "Labelled type"))
        st.plotly_chart(fcm, use_container_width=True)
        st.markdown(T(
            "**읽은 것** — 라벨 오류 5 % 가 있으므로 정확도 상한은 약 95 % 다. 남은 오차 대부분이 이 라벨 오류다. "
            "그래서 다음 단계는 모형 교체보다 실제 민원 문장 수집이다. 4번 민원 페이지의 접수 폼이 이 분류기를 쓴다.",
            "**Reading** — With 5 % label error, the accuracy ceiling is about 95 %; most remaining error is that noise. "
            "The next step is collecting real complaint text, not a new model. The intake form on page 4 uses this classifier."))
        st.dataframe(t["data"].sample(8, random_state=1), hide_index=True, use_container_width=True)
        txt = st.text_input(T("문장을 넣어 보세요", "Try a sentence (Korean)"), value="욕실 천장에서 물이 뚝뚝 떨어져요")
        if txt:
            from ai_validation import predict_complaint_text
            lbl, tab = predict_complaint_text(t["model"], txt)
            st.success(T(f"예측 유형: **{lbl}** (확률 {tab['확률'].iloc[0]:.2f})",
                         f"Predicted: **{TYPE_EN.get(lbl, lbl)}** (p = {tab['확률'].iloc[0]:.2f})"))

    # 한계 · 다시 돌리기
    with tabs[6]:
        st.markdown(T(
            "**가정과 한계**\n\n"
            "- 모든 데이터는 `ai_pipeline.py` · `ai_validation.py` 가 만든 합성 데이터다. 실제 단지 데이터가 아니다.\n"
            "- 시계열 개선 모형은 생성식의 구조(추세 + 계절, 누적 성장)를 안다. 실데이터에서는 구조를 먼저 확인해야 한다.\n"
            "- 위험 등급은 고위험이 7 % 뿐이라 F1 이 fold 마다 크게 흔들린다.\n"
            "- 판정 기준: 개선안은 (1) 5-fold 평균이 기존보다 높고 (2) 시계열은 naive 보다 WAPE 가 낮을 때만 채택한다.",
            "**Assumptions and limits**\n\n"
            "- All data is synthetic, produced by `ai_pipeline.py` and `ai_validation.py`; not real complex data.\n"
            "- Improved time-series models know the generator's structure (trend + season, cumulative growth). Check structure first on real data.\n"
            "- Risk grade has only 7 % high-risk rows, so F1 swings widely across folds.\n"
            "- Decision rule: adopt a change only if (1) its 5-fold mean beats the original and (2) for time series its WAPE beats naive."))
        st.markdown(T("**다시 돌리는 법**", "**How to rerun**"))
        st.code("pip install -r requirements.txt\npython ai_validation.py      # 콘솔 표 · console tables\nstreamlit run app.py         # 10번 페이지 · page 10", language="bash")
        tm = out.get("timing", {})
        st.caption(T("단계별 시간 (초): ", "Step time (s): ") + ", ".join(f"{k} {v:.1f}" for k, v in tm.items()))

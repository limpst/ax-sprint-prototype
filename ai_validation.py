"""
에이톰-AX v2.5 — 검증 · 튜닝 · XAI · 민원 문장 분류
Atom-AX v2.5 — validation, tuning, XAI and complaint-text classification

AXPipelineEngine(ai_pipeline.py)이 만든 합성 데이터를 그대로 받아
1) 분류: stratified 5-fold 로 기존 모형(baseline)과 튜닝한 HGB 를 비교한다 (nested CV).
2) 시계열: 무작위 분할과 walk-forward 분할의 차이를 보이고, feature 개선 효과를 잰다.
3) 이상 탐지: 불균형 데이터에서 accuracy 대신 PR-AUC · F1 을 본다.
4) 확률 보정: Brier score 와 reliability 곡선을 보정 전후로 비교한다.
5) XAI: permutation importance 와 단지별 occlusion 기여도를 낸다.
   위험 점수 생성식이 알려져 있으므로 참값 기여도와 비교한다.
6) 민원 문장: 합성 문장 + TF-IDF(char n-gram) + LogisticRegression.

모든 난수는 seed 2026 에서 파생한다. 결과는 합성 데이터 기준이다.
"""
from __future__ import annotations

import time
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.ensemble import (
    GradientBoostingClassifier, GradientBoostingRegressor,
    HistGradientBoostingClassifier, HistGradientBoostingRegressor,
    IsolationForest, RandomForestClassifier,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score, average_precision_score, brier_score_loss,
    confusion_matrix, f1_score, mean_absolute_error, r2_score,
)
from sklearn.model_selection import (
    GridSearchCV, StratifiedKFold, TimeSeriesSplit, cross_val_predict,
    cross_validate, train_test_split,
)
from sklearn.pipeline import make_pipeline

N_JOBS = 1  # Render free plan = 1 vCPU


def wape(y, p):
    """Weighted Absolute Percentage Error = Σ|y−p| / Σ|y| (0 이 많은 고장 건수에 MAPE 대신 사용)."""
    y = np.asarray(y, float)
    d = np.abs(y).sum()
    return float(np.abs(y - np.asarray(p, float)).sum() / d) if d else float("nan")


def _ms(a):
    a = np.asarray(a, float)
    return float(a.mean()), float(a.std())


# ══════════════════════════════════════════════════════════════
# 1. 민원 문장 합성 · synthetic complaint sentences
# ══════════════════════════════════════════════════════════════
COMPLAINT_TEXT = {
    "누수": {
        "subj": ["천장", "욕실 천장", "베란다 벽", "주방 싱크대 밑", "안방 벽지", "윗집 배관"],
        "verb": ["물이 새요", "물방울이 떨어져요", "젖어 있어요", "습기가 차요", "곰팡이가 생겼어요", "물자국이 번져요"],
    },
    "균열·구조손상": {
        "subj": ["거실 벽", "외벽", "계단실 벽", "기둥", "발코니 난간", "현관 바닥"],
        "verb": ["금이 갔어요", "갈라졌어요", "균열이 커졌어요", "콘크리트가 떨어졌어요", "기울어 보여요", "흔들려요"],
    },
    "화재·가연성외벽": {
        "subj": ["외벽 단열재", "드라이비트 외벽", "복도 전기함", "지하 주차장", "옥상 스티로폼", "분전반"],
        "verb": ["타는 냄새가 나요", "연기가 나요", "불꽃이 튀었어요", "그을음이 보여요", "녹아 있어요", "화재가 걱정돼요"],
    },
    "시설노후": {
        "subj": ["엘리베이터", "현관문 도어락", "보일러", "창틀", "수도꼭지", "복도 조명"],
        "verb": ["고장 났어요", "너무 낡았어요", "교체가 필요해요", "자주 멈춰요", "수리해 주세요", "오래돼서 안 돼요"],
    },
    "관리비이의": {
        "subj": ["이번 달 관리비", "전기료", "수도 요금", "난방비", "공용 전기료", "관리비 청구서"],
        "verb": ["너무 많이 나왔어요", "과다 청구된 것 같아요", "계산이 틀렸어요", "지난달보다 두 배예요", "내역을 알려 주세요", "이의 신청합니다"],
    },
    "계약관련": {
        "subj": ["임대차 계약", "계약 만료일", "재계약", "보증금", "퇴거 일정", "계약 연장"],
        "verb": ["언제인지 알려 주세요", "갱신하고 싶어요", "서류가 뭐가 필요한가요", "반환은 언제 되나요", "조정하고 싶어요", "신청 방법을 알려 주세요"],
    },
    "기타": {
        "subj": ["윗집 소음", "주차 공간", "분리수거장", "복도 벌레", "엘리베이터 냄새", "놀이터"],
        "verb": ["너무 심해요", "부족해요", "지저분해요", "많이 나와요", "불편해요", "정리가 안 돼요"],
    },
}
PREFIX = ["", "", "안녕하세요. ", "급합니다. ", "계속 ", "어제부터 ", "몇 주째 ", "확인 부탁드립니다. "]
SUFFIX = ["", "", " 빨리 와 주세요.", " 사진 첨부합니다.", " 확인 부탁드려요.", " 아이가 있어서 걱정돼요.", " 지난번에도 말씀드렸어요."]
# 다른 유형과 겹치는 문장 조각 → 문제를 일부러 어렵게 만든다
CONFUSERS = ["벽에서", "엘리베이터", "관리사무소에", "물", "냄새", "낡은"]


def gen_complaint_texts(n=700, seed=2026):
    rng = np.random.default_rng(seed + 20)
    types = list(COMPLAINT_TEXT)
    probs = np.array([0.20, 0.15, 0.08, 0.15, 0.15, 0.12, 0.15])
    rows = []
    for i in range(n):
        t = rng.choice(types, p=probs)
        d = COMPLAINT_TEXT[t]
        s = f"{rng.choice(PREFIX)}{rng.choice(d['subj'])}에 {rng.choice(d['verb'])}."
        if rng.random() < 0.35:
            s += f" {rng.choice(CONFUSERS)} 관련해서도 문의드려요."
        if rng.random() < 0.30:  # 부차 민원: 다른 유형 표현이 섞임 · secondary issue from another type
            o = COMPLAINT_TEXT[rng.choice([u for u in types if u != t])]
            s += f" 그리고 {rng.choice(o['subj'])}도 {rng.choice(o['verb'])}"
        s += rng.choice(SUFFIX)
        label = t
        if rng.random() < 0.05:  # 접수 담당자 라벨 오류 5 % · 5 % labelling error
            label = rng.choice([u for u in types if u != t])
        rows.append({"민원번호": f"TX-2026-{i + 1:04d}", "유형": label, "문장": s})
    return pd.DataFrame(rows)


def make_text_model(seed=2026):
    return make_pipeline(
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=2, sublinear_tf=True),
        LogisticRegression(C=4.0, max_iter=2000, class_weight="balanced", random_state=seed),
    )


# ══════════════════════════════════════════════════════════════
# 2. 검증 스위트 · validation suite
# ══════════════════════════════════════════════════════════════
class ValidationSuite:
    """AXPipelineEngine.run_all() 뒤에 호출한다. · Call after AXPipelineEngine.run_all()."""

    HGB_GRID = {"max_depth": [3, None]}

    def __init__(self, engine, seed=2026):
        self.eng = engine
        self.seed = seed
        self.out = {}

    # ── helpers ──
    def _skf(self, k=5):
        return StratifiedKFold(n_splits=k, shuffle=True, random_state=self.seed)

    def _tuned_hgb(self):
        inner = StratifiedKFold(n_splits=3, shuffle=True, random_state=self.seed + 1)
        base = HistGradientBoostingClassifier(max_iter=100, learning_rate=0.1, random_state=self.seed)
        return GridSearchCV(base, self.HGB_GRID, cv=inner, scoring="f1_macro", n_jobs=N_JOBS)

    # ── 2.1 분류 · classification (nested CV) ──
    def classification(self):
        P = self.eng.pipelines
        tasks = [
            ("vision", "비전 손상 7종 · Vision damage (7 classes)", P["vision"]["data"],
             ["균열폭_mm", "길이_cm", "면적_cm2", "텍스처분산", "엣지밀도", "색상차이", "열화상차이", "습윤지수"],
             "손상유형", RandomForestClassifier(n_estimators=100, max_depth=10, random_state=self.seed)),
            ("complaint", "민원 7종 (수치 feature) · Complaints (numeric)", P["complaint"]["data"],
             ["텍스트길이", "긴급키워드수", "감성점수"] + [c for c in P["complaint"]["data"].columns if c.startswith("키워드_")],
             "유형", GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=self.seed)),
            ("risk", "위험 등급 3단계 · Risk grade (3 levels)", P["risk"]["data"],
             ["경과년수", "IoT이상횟수", "균열성장률_mm월", "점검경과일수", "기상위험지수", "드라이비트면적_cm", "민원빈도"],
             "위험등급", GradientBoostingClassifier(n_estimators=120, max_depth=4, random_state=self.seed)),
            ("subsidence", "지반침하 발생 · Subsidence (binary)", P["subsidence"]["data"],
             ["지하수위_m", "30일강수량_mm", "관로경과년수", "투수계수", "InSAR속도_mm년", "GPR공동크기_cm", "진동평균_g"],
             "침하발생", GradientBoostingClassifier(n_estimators=120, max_depth=5, random_state=self.seed)),
        ]
        rows, extra = [], {}
        for key, name, df, feats, target, base in tasks:
            X, y = df[feats].values, df[target].astype(str).values
            scoring = {"f1": "f1_macro", "acc": "accuracy"}
            b = cross_validate(base, X, y, cv=self._skf(), scoring=scoring, n_jobs=N_JOBS)
            t = cross_validate(self._tuned_hgb(), X, y, cv=self._skf(), scoring=scoring,
                               n_jobs=N_JOBS, return_estimator=True)
            best = [e.best_params_ for e in t["estimator"]]
            best_mode = max({str(p): p for p in best}.values(), key=lambda p: sum(str(p) == str(q) for q in best))
            # 혼동행렬 · confusion matrix (out-of-fold, tuned)
            final = HistGradientBoostingClassifier(max_iter=100, learning_rate=0.1, random_state=self.seed, **best_mode)
            oof = cross_val_predict(final, X, y, cv=self._skf(), n_jobs=N_JOBS)
            classes = sorted(np.unique(y))
            extra[key] = {"cm": confusion_matrix(y, oof, labels=classes), "classes": classes}
            bf, tf = _ms(b["test_f1"]), _ms(t["test_f1"])
            rows.append({
                "key": key, "task": name, "n": len(y), "classes": len(classes),
                "majority_acc": float(pd.Series(y).value_counts(normalize=True).iloc[0]),
                "base_model": type(base).__name__,
                "base_f1": bf[0], "base_f1_sd": bf[1], "base_acc": _ms(b["test_acc"])[0],
                "tuned_f1": tf[0], "tuned_f1_sd": tf[1], "tuned_acc": _ms(t["test_acc"])[0],
                "delta_f1": tf[0] - bf[0], "best_params": str(best_mode),
            })
        self.out["classification"] = pd.DataFrame(rows)
        self.out["confusion"] = extra

    # ── 2.2 시계열 · time series (walk-forward) ──
    def timeseries(self):
        P = self.eng.pipelines
        rows, curves = [], {}

        def _rand_r2(model, X, y):
            Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=self.seed)
            return r2_score(yte, clone(model).fit(Xtr, ytr).predict(Xte))

        def _wf(model, X, y, folds):
            yt, yp = [], []
            for tr, te in folds:
                m = clone(model).fit(X[tr], y[tr])
                yt.append(y[te]); yp.append(m.predict(X[te]))
            yt, yp = np.concatenate(yt), np.concatenate(yp)
            return r2_score(yt, yp), mean_absolute_error(yt, yp), wape(yt, yp), yt, yp

        # (a) 고장 · failure — 4 단지 × 36 개월, 월 블록으로 앞으로 이동
        f = P["failure"]["data"].sort_values(["월", "단지"]).reset_index(drop=True)
        f["단지코드"] = f["단지"].astype("category").cat.codes
        f["작년같은달"] = f.groupby("단지")["AI적용후_고장"].shift(12)
        f["전월"] = f.groupby("단지")["AI적용후_고장"].shift(1)
        blocks = [(12, 18), (18, 24), (24, 30), (30, 36)]
        folds = [(np.where(f["월"] < a)[0], np.where((f["월"] >= a) & (f["월"] < b))[0]) for a, b in blocks]
        y = f["AI적용후_고장"].values.astype(float)
        base_feats = ["월", "경과년수", "평균기온", "강수량_mm", "계절요인"]
        gbr = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=self.seed)
        r_rand = _rand_r2(gbr, f[base_feats].values, y)
        r_b = _wf(gbr, f[base_feats].values, y, folds)
        ff = f.fillna({"작년같은달": f["AI적용후_고장"].mean(), "전월": f["AI적용후_고장"].mean()})
        # 추세 + 단지별 계절 진폭: y ≈ a_c·season + b·month + c_c (선형, 외삽 가능)
        dmy = pd.get_dummies(ff["단지"], dtype=float)
        Xi = np.column_stack([ff["월"].values, dmy.values, dmy.values * ff["계절요인"].values[:, None]])
        r_i = _wf(LinearRegression(), Xi, y, folds)  # Ridge 는 12개월 학습 fold 에서 과소적합
        te_idx = np.concatenate([te for _, te in folds])
        naive = ff["전월"].values[te_idx]
        rows.append(self._ts_row("failure", "고장 건수 (월) · Monthly failures", r_rand, r_b, r_i,
                                 wape(y[te_idx], naive), "전월 값 · last month",
                                 "나무 모형 → 추세 + 단지별 계절 진폭 선형 모형 (외삽 가능) · trees → linear model with trend + per-complex seasonal amplitude (extrapolates)"))
        curves["failure"] = {"x": f["월"].values[te_idx], "y": r_i[3], "p_base": r_b[4], "p_imp": r_i[4],
                             "group": f["단지"].values[te_idx]}

        # (b) 에너지 · energy — 365 일, TimeSeriesSplit(5)
        e = P["energy"]["data"].sort_values("일차").reset_index(drop=True)
        e["doy_sin"] = np.sin(2 * np.pi * e["일차"] / 365)
        e["doy_cos"] = np.cos(2 * np.pi * e["일차"] / 365)
        e["난방도일"] = np.clip(18 - e["외기온"], 0, None)
        e["냉방도일"] = np.clip(e["외기온"] - 26, 0, None)
        y = e["총에너지_kWh"].values
        folds = list(TimeSeriesSplit(n_splits=5, test_size=40).split(e))
        base_feats = ["외기온", "습도", "점유율", "주말", "일차"]
        gbr = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=self.seed)
        r_rand = _rand_r2(gbr, e[base_feats].values, y)
        r_b = _wf(gbr, e[base_feats].values, y, folds)
        imp_feats = ["외기온", "점유율", "주말", "doy_sin", "doy_cos", "난방도일", "냉방도일"]
        hgb = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_depth=3, random_state=self.seed)
        r_i = _wf(hgb, e[imp_feats].values, y, folds)
        te_idx = np.concatenate([te for _, te in folds])
        naive = np.r_[y[0], y[:-1]][te_idx]
        rows.append(self._ts_row("energy", "일 전력량 · Daily energy (kWh)", r_rand, r_b, r_i,
                                 wape(y[te_idx], naive), "전일 값 · yesterday",
                                 "`일차` → 계절 sin/cos + 난방·냉방 도일 · day index → seasonal sin/cos + heating/cooling degree"))
        curves["energy"] = {"x": e["일차"].values[te_idx], "y": r_i[3], "p_base": r_b[4], "p_imp": r_i[4]}

        # (c) 균열 · crack — 50 균열 × 12 개월
        c = P["crack"]["data"].sort_values(["월차", "균열ID"]).reset_index(drop=True)
        c["전월폭"] = c.groupby("균열ID")["균열폭_mm"].shift(1)
        c["전월증가"] = c.groupby("균열ID")["균열폭_mm"].diff().shift(1)
        first = c.groupby("균열ID")["균열폭_mm"].transform("first")
        c["평균성장"] = (c["전월폭"] - first) / (c["월차"] - 1).clip(lower=1)
        c["다음증가"] = c["균열폭_mm"] - c["전월폭"]
        c = c[c["월차"] >= 2].reset_index(drop=True)
        y = c["균열폭_mm"].values
        folds = [(np.where(c["월차"] < m)[0], np.where(c["월차"] == m)[0]) for m in range(6, 12)]
        base_feats = ["월차", "초기폭_mm", "기온", "동결해동"]
        gbr = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=self.seed)
        r_rand = _rand_r2(gbr, c[base_feats].values, y)
        r_b = _wf(gbr, c[base_feats].values, y, folds)
        # 증가량 모형: Δw ≈ β1·평균성장 + β2·평균성장·동결해동, 예측폭 = 전월폭 + Δw
        Xi = np.column_stack([c["평균성장"], c["평균성장"] * c["동결해동"]])
        yt_, yp_ = [], []
        for tr, te in folds:
            m = LinearRegression().fit(Xi[tr], c["다음증가"].values[tr])
            yt_.append(y[te]); yp_.append(c["전월폭"].values[te] + m.predict(Xi[te]))
        yt_, yp_ = np.concatenate(yt_), np.concatenate(yp_)
        r_i = (r2_score(yt_, yp_), mean_absolute_error(yt_, yp_), wape(yt_, yp_), yt_, yp_)
        te_idx = np.concatenate([te for _, te in folds])
        naive = c["전월폭"].values[te_idx]
        rows.append(self._ts_row("crack", "균열 폭 (mm) · Crack width (mm)", r_rand, r_b, r_i,
                                 wape(y[te_idx], naive), "전월 폭 · last month",
                                 "폭 대신 증가량 예측: 전월 폭 + 평균 성장률 × 동결해동 보정 · predict increment: last width + mean growth × freeze–thaw"))
        curves["crack"] = {"x": c["월차"].values[te_idx], "y": r_i[3], "p_base": r_b[4], "p_imp": r_i[4]}

        self.out["timeseries"] = pd.DataFrame(rows)
        self.out["ts_curves"] = curves

    @staticmethod
    def _ts_row(key, name, r_rand, r_b, r_i, naive_wape, naive_name, change):
        return {
            "key": key, "task": name,
            "random_r2": r_rand,
            "wf_base_r2": r_b[0], "wf_base_wape": r_b[2],
            "wf_imp_r2": r_i[0], "wf_imp_wape": r_i[2], "wf_imp_mae": r_i[1],
            "naive_wape": naive_wape, "naive": naive_name, "change": change,
        }

    # ── 2.3 이상 탐지 · anomaly (imbalanced) ──
    def anomaly(self):
        P = self.eng.pipelines
        rows, pr = [], {}
        # IoT
        d = P["iot"]["data"]
        X, y = d[["온도", "습도", "전력_kWh", "진동_g", "CO_ppm"]].values, d["이상"].values
        Xs = (X - X.mean(0)) / X.std(0)
        iso = IsolationForest(n_estimators=200, contamination="auto", random_state=self.seed).fit(Xs)
        s_iso = -iso.score_samples(Xs)
        z = np.abs(Xs).max(1)  # 단순 z-score 최대값 · max |z|
        rows.append(self._anom_row("iot", "IoT 센서 이상 · IoT sensor anomaly", y, {
            "IsolationForest": s_iso, "max |z| 규칙 · rule": z}))
        pr["iot"] = (y, s_iso)
        # 관리비 · billing
        d = P["billing"]["data"]
        feats = ["면적_m2", "세대원수", "관리비_만원", "전기료_만원", "수도료_만원", "총청구_만원"]
        X, y = d[feats].values.astype(float), d["이상청구"].values
        d2 = d.copy()
        d2["관리비_per_m2"] = d["관리비_만원"] / d["면적_m2"]
        d2["전기_per_인"] = d["전기료_만원"] / d["세대원수"]
        d2["수도_per_인"] = d["수도료_만원"] / d["세대원수"]
        X2 = d2[feats + ["관리비_per_m2", "전기_per_인", "수도_per_인"]].values.astype(float)
        Xs = (X - X.mean(0)) / X.std(0)
        X2s = (X2 - X2.mean(0)) / X2.std(0)
        s_iso = -IsolationForest(n_estimators=200, random_state=self.seed).fit(Xs).score_samples(Xs)
        s_iso2 = -IsolationForest(n_estimators=200, random_state=self.seed).fit(X2s).score_samples(X2s)
        rf = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=self.seed)
        s_rf = cross_val_predict(rf, X2, y, cv=self._skf(), method="predict_proba", n_jobs=N_JOBS)[:, 1]
        rows.append(self._anom_row("billing", "관리비 이상 청구 · Billing anomaly", y, {
            "IsolationForest (원 feature · raw)": s_iso,
            "IsolationForest + 비율 feature · ratios": s_iso2,
            "RF balanced (지도 · supervised, 5-fold)": s_rf}))
        pr["billing"] = (y, s_iso2)
        self.out["anomaly"] = pd.concat(rows, ignore_index=True)
        self.out["anomaly_pr"] = pr

    @staticmethod
    def _anom_row(key, name, y, scores):
        out = []
        k = int(y.sum())
        for mname, s in scores.items():
            top = np.zeros_like(y)
            top[np.argsort(-s)[:k]] = 1
            out.append({"key": key, "task": name, "method": mname, "n": len(y),
                        "base_rate": float(y.mean()), "pr_auc": average_precision_score(y, s),
                        "f1_at_k": f1_score(y, top), "acc_all_normal": 1 - float(y.mean())})
        return pd.DataFrame(out)

    # ── 2.4 확률 보정 · calibration ──
    def calibration(self):
        d = self.eng.pipelines["subsidence"]["data"]
        feats = ["지하수위_m", "30일강수량_mm", "관로경과년수", "투수계수", "InSAR속도_mm년", "GPR공동크기_cm", "진동평균_g"]
        X, y = d[feats].values, d["침하발생"].values
        raw = GradientBoostingClassifier(n_estimators=120, max_depth=5, random_state=self.seed)
        cal = CalibratedClassifierCV(clone(raw), method="sigmoid", cv=5)
        p_raw = cross_val_predict(raw, X, y, cv=self._skf(), method="predict_proba", n_jobs=N_JOBS)[:, 1]
        p_cal = cross_val_predict(cal, X, y, cv=self._skf(), method="predict_proba", n_jobs=N_JOBS)[:, 1]
        curves = {}
        for nm, p in (("raw", p_raw), ("cal", p_cal)):
            fr, mp = calibration_curve(y, p, n_bins=8, strategy="quantile")
            curves[nm] = (mp, fr)
        self.out["calibration"] = {
            "task": "지반침하 발생 확률 · Subsidence probability",
            "brier_raw": brier_score_loss(y, p_raw), "brier_cal": brier_score_loss(y, p_cal),
            "brier_climatology": brier_score_loss(y, np.full_like(p_raw, y.mean(), dtype=float)),
            "curves": curves, "n": len(y), "base_rate": float(y.mean()),
        }

    # ── 2.5 XAI ──
    RISK_W = {"경과년수": 0.3, "IoT이상횟수": 5, "균열성장률_mm월": 30, "점검경과일수": 0.2,
              "기상위험지수": 10, "드라이비트면적_cm": 0.05, "민원빈도": 3}

    def xai(self):
        d = self.eng.pipelines["risk"]["data"]
        feats = list(self.RISK_W)
        X, y = d[feats].values, d["위험점수"].values
        Xtr, Xte, ytr, yte, dtr, dte = train_test_split(X, y, d, test_size=0.25, random_state=self.seed)
        reg = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=self.seed).fit(Xtr, ytr)
        pi = permutation_importance(reg, Xte, yte, n_repeats=20, random_state=self.seed, scoring="r2", n_jobs=N_JOBS)
        perm = pd.DataFrame({"feature": feats, "mean": pi.importances_mean, "std": pi.importances_std})
        perm = perm.sort_values("mean", ascending=False).reset_index(drop=True)
        # 단지별 occlusion 기여도: f(x) − f(x_j ← 학습 중앙값) · per-complex occlusion contribution
        med = np.median(Xtr, axis=0)
        cpx = d.groupby("단지")[feats].mean()
        local = []
        for name, row in cpx.iterrows():
            x = row.values.astype(float)
            fx = reg.predict(x[None])[0]
            for j, ft in enumerate(feats):
                xm = x.copy(); xm[j] = med[j]
                local.append({"단지": name, "feature": ft, "model": fx - reg.predict(xm[None])[0],
                              "true": self.RISK_W[ft] * (x[j] - med[j]), "score": fx})
        local = pd.DataFrame(local)
        corr = float(np.corrcoef(local["model"], local["true"])[0, 1])
        self.out["xai"] = {"perm": perm, "local": local, "corr_true": corr,
                           "test_r2": r2_score(yte, reg.predict(Xte)), "median": dict(zip(feats, med))}

    # ── 2.6 민원 문장 · complaint text ──
    def text(self):
        df = gen_complaint_texts(700, self.seed)
        X, y = df["문장"].values, df["유형"].values
        model = make_text_model(self.seed)
        cv = cross_validate(model, X, y, cv=self._skf(), scoring={"f1": "f1_macro", "acc": "accuracy"}, n_jobs=N_JOBS)
        oof = cross_val_predict(model, X, y, cv=self._skf(), n_jobs=N_JOBS)
        classes = sorted(np.unique(y))
        final = make_text_model(self.seed).fit(X, y)
        self.out["text"] = {
            "data": df, "f1": _ms(cv["test_f1"]), "acc": _ms(cv["test_acc"]),
            "cm": confusion_matrix(y, oof, labels=classes), "classes": classes, "model": final,
        }

    def run_all(self):
        t0 = time.time()
        for step in (self.classification, self.timeseries, self.anomaly, self.calibration, self.xai, self.text):
            t = time.time(); step(); self.out.setdefault("timing", {})[step.__name__] = time.time() - t
        self.out["elapsed"] = time.time() - t0
        return self.out


def predict_complaint_text(model, text):
    """학습된 문장 분류기로 (유형, 확률표) 반환 · returns (label, probability table)."""
    p = model.predict_proba([text])[0]
    tab = pd.DataFrame({"유형": model.classes_, "확률": p}).sort_values("확률", ascending=False)
    return tab.iloc[0]["유형"], tab.reset_index(drop=True)


if __name__ == "__main__":
    import sys
    from ai_pipeline import AXPipelineEngine
    eng = AXPipelineEngine(seed=2026); eng.run_all()
    out = ValidationSuite(eng).run_all()
    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
    print(out["classification"].drop(columns=["task"]).round(3).to_string())
    print(out["timeseries"].drop(columns=["task", "change", "naive"]).round(3).to_string())
    print(out["anomaly"].drop(columns=["task"]).round(3).to_string())
    c = out["calibration"]; print("brier raw/cal/clim", round(c["brier_raw"], 4), round(c["brier_cal"], 4), round(c["brier_climatology"], 4))
    x = out["xai"]; print(x["perm"].round(3).to_string()); print("corr_true", round(x["corr_true"], 3), "r2", round(x["test_r2"], 3))
    t = out["text"]; print("text f1", t["f1"], "acc", t["acc"])
    print(predict_complaint_text(t["model"], "욕실 천장에서 물이 뚝뚝 떨어져요")[0])
    print("timing", {k: round(v, 1) for k, v in out["timing"].items()}, "total", round(out["elapsed"], 1))

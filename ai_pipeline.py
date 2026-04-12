"""
에이톰-AX AI 데이터 파이프라인 엔진 v1.0.3
55개 파이프라인 — Mock 데이터 생성 · 모델 학습 · 추론 · 평가
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import (
    RandomForestClassifier, GradientBoostingClassifier,
    IsolationForest, RandomForestRegressor, GradientBoostingRegressor
)
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    mean_absolute_error, mean_squared_error, r2_score,
    classification_report, confusion_matrix
)
import warnings
warnings.filterwarnings('ignore')


class AXPipelineEngine:
    """에이톰-AX 55개 AI 파이프라인 실행 엔진"""

    def __init__(self, seed=2026):
        self.seed = seed
        np.random.seed(seed)
        self.results = {}

    # ════════════════════════════════════════════════════════
    # 1. 비전 AI — 드론·앱 시설물 손상 이미지 (P-001~P-010)
    # ════════════════════════════════════════════════════════
    def gen_vision_data(self, n=500):
        """드론·앱 촬영 이미지 특징 추출 시뮬 데이터"""
        np.random.seed(self.seed)
        damage_types = ["수직균열", "수평균열", "누수흔적", "드라이비트화재", "박리손상", "표면박락", "정상"]
        risk_map = {"수직균열": 2, "수평균열": 0, "누수흔적": 1, "드라이비트화재": 2, "박리손상": 2, "표면박락": 1, "정상": 0}
        data = []
        for i in range(n):
            dtype = np.random.choice(damage_types, p=[0.15, 0.10, 0.15, 0.10, 0.10, 0.10, 0.30])
            is_damage = dtype != "정상"
            crack_width = np.clip(np.random.exponential(0.2) + (0.15 if is_damage else 0), 0, 3.0) if dtype in ["수직균열","수평균열","박리손상","표면박락"] else 0
            length_cm = np.clip(np.random.exponential(20) + (10 if is_damage else 0), 0, 200)
            area_cm2 = np.clip(np.random.exponential(50) + (30 if is_damage else 0), 0, 2000)
            texture_var = np.random.uniform(0.1, 0.9) + (0.3 if is_damage else 0)
            edge_density = np.random.uniform(0.05, 0.5) + (0.2 if is_damage else 0)
            color_diff = np.random.uniform(0, 50) + (20 if dtype in ["누수흔적", "드라이비트화재"] else 0)
            thermal_diff = np.random.uniform(0, 5) + (3 if dtype == "드라이비트화재" else 0)
            moisture = np.random.uniform(0, 30) + (25 if dtype == "누수흔적" else 0)
            method = np.random.choice(["드론스캔", "앱업로드"], p=[0.6, 0.4])
            complex_name = np.random.choice(["강남A동","마포B동","서초E동","노원C동","강서D동","구미A동","안동B동"])
            data.append({
                "sample_id": f"IMG-{i+1:04d}",
                "단지": complex_name,
                "촬영방식": method,
                "균열폭_mm": round(crack_width, 3),
                "길이_cm": round(length_cm, 1),
                "면적_cm2": round(area_cm2, 1),
                "텍스처분산": round(min(texture_var, 1.0), 3),
                "엣지밀도": round(min(edge_density, 0.8), 3),
                "색상차이": round(min(color_diff, 80), 1),
                "열화상차이": round(thermal_diff, 2),
                "습윤지수": round(min(moisture, 60), 1),
                "손상유형": dtype,
                "위험도": risk_map[dtype],  # 0=저, 1=중, 2=고
            })
        return pd.DataFrame(data)

    def train_vision_model(self, df):
        """Y-MaskNet 시뮬 — 손상 유형 7종 분류 (RandomForest)"""
        features = ["균열폭_mm","길이_cm","면적_cm2","텍스처분산","엣지밀도","색상차이","열화상차이","습윤지수"]
        X = df[features].values
        le = LabelEncoder()
        y = le.fit_transform(df["손상유형"])
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=self.seed, stratify=y)
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        model = RandomForestClassifier(n_estimators=100, random_state=self.seed, max_depth=10)
        model.fit(X_train_s, y_train)
        y_pred = model.predict(X_test_s)
        y_prob = model.predict_proba(X_test_s)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        cm = confusion_matrix(y_test, y_pred)
        fi = dict(zip(features, model.feature_importances_))
        fi_sorted = dict(sorted(fi.items(), key=lambda x: x[1], reverse=True))
        result = {
            "model_name": "Y-MaskNet 시뮬 (RandomForest)",
            "accuracy": round(acc, 4),
            "f1_score": round(f1, 4),
            "confusion_matrix": cm,
            "feature_importance": fi_sorted,
            "classes": le.classes_.tolist(),
            "n_train": len(X_train),
            "n_test": len(X_test),
            "predictions": y_pred,
            "probabilities": y_prob,
            "y_test": y_test,
            "model": model,
            "scaler": scaler,
            "encoder": le,
        }
        self.results["vision"] = result
        return result

    # ════════════════════════════════════════════════════════
    # 2. IoT 센서 이상 탐지 (P-011~P-018)
    # ════════════════════════════════════════════════════════
    def gen_iot_data(self, n_hours=720):
        """IoT 5개 센서 시계열 + 이상 라벨"""
        np.random.seed(self.seed + 1)
        data = []
        for h in range(n_hours):
            ts = datetime.now() - timedelta(hours=(n_hours - h))
            temp = 21 + 7 * np.sin(h / 24 * np.pi) + np.random.normal(0, 0.5)
            humidity = 54 + 18 * np.sin(h / 24 * np.pi + 0.8) + np.random.normal(0, 1.5)
            power = max(0, 2.1 + 1.5 * np.sin(h / 24 * np.pi + 0.5) + np.random.normal(0, 0.3))
            vibration = abs(np.random.normal(0, 0.15))
            co = max(0, 1.8 + abs(np.random.normal(0, 0.3)))
            # 이상값 삽입
            if 190 < h < 210: vibration += 0.85
            if 390 < h < 402: co += 16
            if 480 < h < 490: temp += 12
            if 550 < h < 558: humidity += 25
            if 620 < h < 625: power += 4.5
            anomaly = 1 if (temp > 30 or humidity > 72 or vibration > 0.5 or co > 10 or power > 4.5) else 0
            data.append({
                "ts": ts, "시간": h,
                "온도": round(temp, 2), "습도": round(humidity, 2),
                "전력_kWh": round(power, 3), "진동_g": round(vibration, 4),
                "CO_ppm": round(co, 2), "이상": anomaly,
            })
        return pd.DataFrame(data)

    def train_iot_anomaly_model(self, df):
        """IoT 이상 탐지 — IsolationForest + RandomForest 분류"""
        features = ["온도", "습도", "전력_kWh", "진동_g", "CO_ppm"]
        X = df[features].values
        y = df["이상"].values
        scaler = StandardScaler()
        X_s = scaler.fit_transform(X)
        # IsolationForest (비지도)
        iso = IsolationForest(contamination=0.08, random_state=self.seed, n_estimators=100)
        iso_pred = iso.fit_predict(X_s)
        iso_labels = (iso_pred == -1).astype(int)
        # RandomForest (지도)
        X_train, X_test, y_train, y_test = train_test_split(X_s, y, test_size=0.2, random_state=self.seed)
        rf = RandomForestClassifier(n_estimators=80, random_state=self.seed, max_depth=8)
        rf.fit(X_train, y_train)
        y_pred = rf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        fi = dict(zip(features, rf.feature_importances_))
        anomaly_events = df[df["이상"] == 1][["시간", "온도", "습도", "전력_kWh", "진동_g", "CO_ppm"]].head(10)
        result = {
            "model_name": "IoT 이상 탐지 (IsolationForest + RandomForest)",
            "accuracy": round(acc, 4), "f1_score": round(f1, 4),
            "precision": round(prec, 4), "recall": round(rec, 4),
            "feature_importance": dict(sorted(fi.items(), key=lambda x: x[1], reverse=True)),
            "n_anomalies": int(y.sum()),
            "anomaly_rate": round(y.mean() * 100, 2),
            "anomaly_events": anomaly_events,
            "iso_anomalies": int(iso_labels.sum()),
            "model": rf, "iso_model": iso, "scaler": scaler,
        }
        self.results["iot"] = result
        return result

    # ════════════════════════════════════════════════════════
    # 3. 민원 데이터 분류 (P-019~P-024)
    # ════════════════════════════════════════════════════════
    def gen_complaint_data(self, n=500):
        """민원 텍스트 시뮬 데이터 (키워드 기반 특징)"""
        np.random.seed(self.seed + 2)
        types = ["누수", "균열·구조손상", "화재·가연성외벽", "시설노후", "관리비이의", "계약관련", "기타"]
        risk_map = {"누수": 1, "균열·구조손상": 2, "화재·가연성외벽": 2, "시설노후": 0, "관리비이의": 0, "계약관련": 0, "기타": 0}
        keywords_map = {
            "누수": ["물방울", "천장", "젖어", "습기", "배관", "물이", "새다"],
            "균열·구조손상": ["금", "갈라", "떨어짐", "위험", "벽", "기울", "흔들"],
            "화재·가연성외벽": ["화재", "불", "외벽", "스티로폼", "드라이비트", "연기"],
            "시설노후": ["낡은", "오래된", "고장", "교체", "노후", "수리"],
            "관리비이의": ["관리비", "청구", "과다", "요금", "전기료", "수도"],
            "계약관련": ["계약", "만료", "갱신", "이사", "퇴거", "연장"],
            "기타": ["소음", "주차", "쓰레기", "벌레", "냄새", "이웃"],
        }
        data = []
        for i in range(n):
            ctype = np.random.choice(types, p=[0.20, 0.15, 0.08, 0.15, 0.15, 0.12, 0.15])
            kws = keywords_map[ctype]
            # 키워드 빈도 특징 벡터
            kw_features = {}
            for t, kw_list in keywords_map.items():
                for kw in kw_list:
                    freq = np.random.poisson(3) if t == ctype else np.random.poisson(0.3)
                    kw_features[f"kw_{kw}"] = freq
            # 추가 특징
            text_len = np.random.randint(10, 200) + (50 if risk_map[ctype] >= 1 else 0)
            urgency_words = np.random.poisson(2) + (3 if risk_map[ctype] == 2 else 0)
            sentiment = np.random.uniform(-1, 0) if risk_map[ctype] >= 1 else np.random.uniform(-0.5, 0.5)
            row = {
                "민원번호": f"CM-{2026}-{1000+i:04d}",
                "유형": ctype,
                "위험도": risk_map[ctype],
                "텍스트길이": text_len,
                "긴급키워드수": urgency_words,
                "감성점수": round(sentiment, 3),
            }
            # 각 유형별 키워드 합산 (7개 유형 × 1개 합산 = 7 피처)
            for t, kw_list in keywords_map.items():
                row[f"키워드_{t[:2]}"] = sum(kw_features.get(f"kw_{kw}", 0) for kw in kw_list)
            data.append(row)
        return pd.DataFrame(data)

    def train_complaint_model(self, df):
        """민원 자동 분류 — GradientBoosting (KoBERT 시뮬)"""
        feature_cols = ["텍스트길이", "긴급키워드수", "감성점수"] + [c for c in df.columns if c.startswith("키워드_")]
        X = df[feature_cols].values
        le = LabelEncoder()
        y = le.fit_transform(df["유형"])
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=self.seed, stratify=y)
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        model = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=self.seed)
        model.fit(X_train_s, y_train)
        y_pred = model.predict(X_test_s)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        cm = confusion_matrix(y_test, y_pred)
        fi = dict(zip(feature_cols, model.feature_importances_))
        # 위험도 분류 (별도 모델)
        y_risk = df["위험도"].values
        X_train_r, X_test_r, yr_train, yr_test = train_test_split(X, y_risk, test_size=0.2, random_state=self.seed)
        risk_model = RandomForestClassifier(n_estimators=80, random_state=self.seed)
        risk_model.fit(scaler.fit_transform(X_train_r), yr_train)
        yr_pred = risk_model.predict(scaler.transform(X_test_r))
        risk_acc = accuracy_score(yr_test, yr_pred)
        result = {
            "model_name": "민원 자동 분류 (GradientBoosting, KoBERT 시뮬)",
            "accuracy": round(acc, 4), "f1_score": round(f1, 4),
            "confusion_matrix": cm,
            "feature_importance": dict(sorted(fi.items(), key=lambda x: x[1], reverse=True)),
            "classes": le.classes_.tolist(),
            "risk_accuracy": round(risk_acc, 4),
            "n_train": len(X_train), "n_test": len(X_test),
        }
        self.results["complaint"] = result
        return result

    # ════════════════════════════════════════════════════════
    # 4. 위험도 스코어링 (P-048, XAI)
    # ════════════════════════════════════════════════════════
    def gen_risk_data(self, n=300):
        """단지별 위험도 스코어링 데이터"""
        np.random.seed(self.seed + 3)
        complexes = ["강남A동","마포B동","서초E동","노원C동","강서D동","구미A동","안동B동"]
        ages = [28, 25, 30, 22, 8, 24, 21]
        data = []
        for i in range(n):
            idx = i % 7
            cpx = complexes[idx]
            age = ages[idx] + np.random.uniform(-1, 1)
            iot_anomalies = np.random.poisson(age / 5)
            crack_growth = np.random.exponential(0.05) * age / 10
            inspection_gap = np.random.randint(5, 120)
            weather_risk = np.random.uniform(0, 1)
            drybit_area = np.random.uniform(0, 500) if idx in [2, 5] else np.random.uniform(0, 50)
            complaint_freq = np.random.poisson(age / 8)
            # 실제 위험 이벤트 (라벨)
            risk_score = (age * 0.3 + iot_anomalies * 5 + crack_growth * 30 +
                         inspection_gap * 0.2 + weather_risk * 10 +
                         drybit_area * 0.05 + complaint_freq * 3)
            risk_label = 2 if risk_score > 35 else (1 if risk_score > 20 else 0)
            data.append({
                "단지": cpx, "경과년수": round(age, 1),
                "IoT이상횟수": iot_anomalies,
                "균열성장률_mm월": round(crack_growth, 4),
                "점검경과일수": inspection_gap,
                "기상위험지수": round(weather_risk, 3),
                "드라이비트면적_cm": round(drybit_area, 1),
                "민원빈도": complaint_freq,
                "위험점수": round(risk_score, 2),
                "위험등급": risk_label,
            })
        return pd.DataFrame(data)

    def train_risk_model(self, df):
        """XAI 위험도 스코어링 — GradientBoosting + Feature Importance"""
        features = ["경과년수","IoT이상횟수","균열성장률_mm월","점검경과일수","기상위험지수","드라이비트면적_cm","민원빈도"]
        X = df[features].values
        y = df["위험등급"].values
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=self.seed, stratify=y)
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        model = GradientBoostingClassifier(n_estimators=120, max_depth=4, random_state=self.seed)
        model.fit(X_train_s, y_train)
        y_pred = model.predict(X_test_s)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        fi = dict(zip(features, model.feature_importances_))
        # 회귀 모델 (점수 예측)
        y_score = df["위험점수"].values
        X_tr, X_te, ys_tr, ys_te = train_test_split(X, y_score, test_size=0.2, random_state=self.seed)
        reg = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=self.seed)
        reg.fit(scaler.fit_transform(X_tr), ys_tr)
        ys_pred = reg.predict(scaler.transform(X_te))
        r2 = r2_score(ys_te, ys_pred)
        mae = mean_absolute_error(ys_te, ys_pred)
        result = {
            "model_name": "XAI 위험도 스코어링 (GradientBoosting)",
            "classification_accuracy": round(acc, 4),
            "classification_f1": round(f1, 4),
            "regression_r2": round(r2, 4),
            "regression_mae": round(mae, 2),
            "feature_importance": dict(sorted(fi.items(), key=lambda x: x[1], reverse=True)),
            "score_predictions": ys_pred[:20],
            "score_actuals": ys_te[:20],
            "model": model, "regressor": reg, "scaler": scaler,
        }
        self.results["risk"] = result
        return result

    # ════════════════════════════════════════════════════════
    # 5. 고장 예측 시계열 (P-036, P-039)
    # ════════════════════════════════════════════════════════
    def gen_failure_data(self, n_months=36):
        """시설물 고장 시계열 데이터"""
        np.random.seed(self.seed + 4)
        complexes = ["강남A동","마포B동","노원C동","강서D동"]
        ages = [28, 25, 22, 8]
        data = []
        for ci, cpx in enumerate(complexes):
            base = ages[ci] / 5
            for m in range(n_months):
                season_factor = 1 + 0.3 * np.sin(m / 6 * np.pi)
                failures = max(0, round(base * season_factor + m * 0.15 + np.random.normal(0, 0.8)))
                prev_failures = max(0, round(base * 1.3 * season_factor + m * 0.2 + np.random.normal(0, 0.8)))
                temp_avg = 15 + 12 * np.sin((m + 3) / 6 * np.pi) + np.random.normal(0, 2)
                rain_mm = max(0, 80 + 60 * np.sin((m + 1) / 6 * np.pi) + np.random.normal(0, 20))
                age_at_m = ages[ci] + m / 12
                data.append({
                    "단지": cpx, "월": m, "경과년수": round(age_at_m, 1),
                    "평균기온": round(temp_avg, 1), "강수량_mm": round(rain_mm, 1),
                    "계절요인": round(season_factor, 3),
                    "AI적용후_고장": failures,
                    "AI적용전_고장": prev_failures,
                })
        return pd.DataFrame(data)

    def train_failure_model(self, df):
        """고장 예측 — GradientBoostingRegressor (시계열 회귀)"""
        features = ["월", "경과년수", "평균기온", "강수량_mm", "계절요인"]
        X = df[features].values
        y = df["AI적용후_고장"].values
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=self.seed)
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=self.seed)
        model.fit(X_train_s, y_train)
        y_pred = model.predict(X_test_s)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        fi = dict(zip(features, model.feature_importances_))
        # AI 적용 전후 비교
        before = df["AI적용전_고장"].mean()
        after = df["AI적용후_고장"].mean()
        reduction = round((before - after) / before * 100, 1)
        result = {
            "model_name": "고장 예측 (GradientBoostingRegressor)",
            "r2_score": round(r2, 4), "mae": round(mae, 2), "rmse": round(rmse, 2),
            "feature_importance": dict(sorted(fi.items(), key=lambda x: x[1], reverse=True)),
            "reduction_pct": reduction,
            "before_avg": round(before, 2), "after_avg": round(after, 2),
            "predictions": y_pred, "actuals": y_test,
            "model": model, "scaler": scaler,
        }
        self.results["failure"] = result
        return result

    # ════════════════════════════════════════════════════════
    # 6. 에너지 최적화 (P-027, P-047)
    # ════════════════════════════════════════════════════════
    def gen_energy_data(self, n_days=365):
        """에너지 사용 시뮬 데이터 (365일)"""
        np.random.seed(self.seed + 5)
        data = []
        for d in range(n_days):
            hour_of_year = d * 24
            temp = 12 + 14 * np.sin((d - 90) / 365 * 2 * np.pi) + np.random.normal(0, 3)
            humidity = 55 + 20 * np.sin((d - 60) / 365 * 2 * np.pi) + np.random.normal(0, 5)
            is_weekend = (d % 7) in [5, 6]
            occupancy = 0.4 + 0.3 * (not is_weekend) + np.random.uniform(-0.1, 0.1)
            # 에너지 소비 모델
            heating = max(0, (18 - temp) * 3.5) if temp < 18 else 0
            cooling = max(0, (temp - 26) * 4.0) if temp > 26 else 0
            base_load = 120 + np.random.normal(0, 10)
            lighting = 40 * occupancy + np.random.normal(0, 5)
            total = base_load + heating + cooling + lighting + np.random.normal(0, 15)
            # AI 최적화 후
            optimized = total * np.random.uniform(0.82, 0.90)
            data.append({
                "일차": d, "외기온": round(temp, 1), "습도": round(humidity, 1),
                "점유율": round(occupancy, 2), "주말": int(is_weekend),
                "난방부하": round(heating, 1), "냉방부하": round(cooling, 1),
                "기저부하": round(base_load, 1), "조명부하": round(lighting, 1),
                "총에너지_kWh": round(total, 1),
                "AI최적화_kWh": round(optimized, 1),
            })
        return pd.DataFrame(data)

    def train_energy_model(self, df):
        """에너지 예측 + 최적화 — GBR"""
        features = ["외기온", "습도", "점유율", "주말", "일차"]
        X = df[features].values
        y = df["총에너지_kWh"].values
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=self.seed)
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        model = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=self.seed)
        model.fit(X_train_s, y_train)
        y_pred = model.predict(X_test_s)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        fi = dict(zip(features, model.feature_importances_))
        total_before = df["총에너지_kWh"].sum()
        total_after = df["AI최적화_kWh"].sum()
        saving_pct = round((total_before - total_after) / total_before * 100, 1)
        saving_kwh = round(total_before - total_after, 0)
        result = {
            "model_name": "에너지 예측·최적화 (GBR)",
            "r2_score": round(r2, 4), "mae": round(mae, 2),
            "feature_importance": dict(sorted(fi.items(), key=lambda x: x[1], reverse=True)),
            "saving_pct": saving_pct, "saving_kwh": saving_kwh,
            "total_before": round(total_before, 0), "total_after": round(total_after, 0),
            "predictions": y_pred, "actuals": y_test,
        }
        self.results["energy"] = result
        return result

    # ════════════════════════════════════════════════════════
    # 7. 관리비 이상 탐지 (P-041, P-046)
    # ════════════════════════════════════════════════════════
    def gen_billing_data(self, n=1000):
        """관리비 청구 데이터 + 이상 청구 라벨"""
        np.random.seed(self.seed + 6)
        data = []
        for i in range(n):
            unit_size = np.random.choice([59, 74, 84, 102, 115])
            people = np.random.randint(1, 6)
            mgmt = round(unit_size * 0.18 + np.random.normal(0, 1.5), 1)
            elec = round(people * 2.5 + np.random.normal(0, 1), 1)
            water = round(people * 0.8 + np.random.normal(0, 0.3), 1)
            # 이상값 삽입 (5%)
            is_anomaly = np.random.random() < 0.05
            if is_anomaly:
                choice = np.random.choice(["mgmt", "elec", "water"])
                if choice == "mgmt": mgmt *= np.random.uniform(2, 4)
                elif choice == "elec": elec *= np.random.uniform(2.5, 5)
                else: water *= np.random.uniform(3, 6)
            total = max(0, mgmt) + max(0, elec) + max(0, water)
            overdue_months = np.random.choice([0]*85 + [1]*8 + [2]*4 + [3]*2 + [4]*1)
            data.append({
                "세대번호": f"H-{i+1:04d}",
                "면적_m2": unit_size, "세대원수": people,
                "관리비_만원": round(max(0, mgmt), 1),
                "전기료_만원": round(max(0, elec), 1),
                "수도료_만원": round(max(0, water), 1),
                "총청구_만원": round(total, 1),
                "연체개월": overdue_months,
                "이상청구": int(is_anomaly),
            })
        return pd.DataFrame(data)

    def train_billing_model(self, df):
        """관리비 이상 탐지 — IsolationForest + 연체 예측 LogisticRegression"""
        features = ["면적_m2", "세대원수", "관리비_만원", "전기료_만원", "수도료_만원", "총청구_만원"]
        X = df[features].values
        y_anomaly = df["이상청구"].values
        scaler = StandardScaler()
        X_s = scaler.fit_transform(X)
        # 이상 탐지
        iso = IsolationForest(contamination=0.06, random_state=self.seed)
        iso_pred = iso.fit_predict(X_s)
        iso_labels = (iso_pred == -1).astype(int)
        # 분류
        X_train, X_test, y_train, y_test = train_test_split(X_s, y_anomaly, test_size=0.2, random_state=self.seed)
        clf = RandomForestClassifier(n_estimators=80, random_state=self.seed)
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        # 연체 예측
        y_overdue = (df["연체개월"] > 0).astype(int).values
        X_all = np.column_stack([X, df["연체개월"].values.reshape(-1,1)])
        feat_overdue = features + ["연체개월"]
        X_tr2, X_te2, yo_tr, yo_te = train_test_split(X_s, y_overdue, test_size=0.2, random_state=self.seed)
        lr = LogisticRegression(random_state=self.seed, max_iter=500)
        lr.fit(X_tr2, yo_tr)
        yo_pred = lr.predict(X_te2)
        overdue_acc = accuracy_score(yo_te, yo_pred)
        result = {
            "model_name": "관리비 이상탐지 + 연체예측",
            "anomaly_accuracy": round(acc, 4),
            "iso_detected": int(iso_labels.sum()),
            "actual_anomalies": int(y_anomaly.sum()),
            "overdue_accuracy": round(overdue_acc, 4),
            "overdue_rate": round(y_overdue.mean() * 100, 1),
        }
        self.results["billing"] = result
        return result

    # ════════════════════════════════════════════════════════
    # 8. 균열 성장 예측 (P-036, P-010)
    # ════════════════════════════════════════════════════════
    def gen_crack_growth_data(self, n_cracks=50, n_months=12):
        """균열 성장 시계열 데이터"""
        np.random.seed(self.seed + 7)
        data = []
        for c in range(n_cracks):
            initial_width = np.random.uniform(0.05, 0.3)
            growth_rate = np.random.exponential(0.02)  # mm/월
            is_active = growth_rate > 0.03
            for m in range(n_months):
                width = initial_width + growth_rate * m + np.random.normal(0, 0.005)
                temp = 15 + 12 * np.sin((m + 3) / 6 * np.pi)
                freeze_thaw = max(0, 5 - temp) * 0.1
                width += freeze_thaw * growth_rate
                width = max(0, width)
                data.append({
                    "균열ID": f"CR-{c+1:03d}", "월차": m,
                    "균열폭_mm": round(width, 4),
                    "초기폭_mm": round(initial_width, 4),
                    "성장률_mm월": round(growth_rate, 5),
                    "기온": round(temp, 1),
                    "동결해동": round(freeze_thaw, 3),
                    "활성여부": int(is_active),
                })
        return pd.DataFrame(data)

    def train_crack_model(self, df):
        """균열 성장 예측 — GBR 시계열 + 활성 분류"""
        features = ["월차", "초기폭_mm", "기온", "동결해동"]
        X = df[features].values
        y = df["균열폭_mm"].values
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=self.seed)
        scaler = StandardScaler()
        model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=self.seed)
        model.fit(scaler.fit_transform(X_train), y_train)
        y_pred = model.predict(scaler.transform(X_test))
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        fi = dict(zip(features, model.feature_importances_))
        # 활성 분류
        y_active = df["활성여부"].values
        Xa_tr, Xa_te, ya_tr, ya_te = train_test_split(X, y_active, test_size=0.2, random_state=self.seed)
        clf = RandomForestClassifier(n_estimators=80, random_state=self.seed)
        clf.fit(scaler.fit_transform(Xa_tr), ya_tr)
        ya_pred = clf.predict(scaler.transform(Xa_te))
        active_acc = accuracy_score(ya_te, ya_pred)
        active_f1 = f1_score(ya_te, ya_pred)
        # 6개월 예측 (샘플)
        sample_crack = df[df["균열ID"] == "CR-001"]
        last_month = sample_crack["월차"].max()
        future = []
        for fm in range(1, 7):
            fut_temp = 15 + 12 * np.sin((last_month + fm + 3) / 6 * np.pi)
            fut_ft = max(0, 5 - fut_temp) * 0.1
            fut_x = scaler.transform([[last_month + fm, sample_crack["초기폭_mm"].iloc[0], fut_temp, fut_ft]])
            fut_pred = model.predict(fut_x)[0]
            future.append({"월차": last_month + fm, "예측폭_mm": round(fut_pred, 4)})
        result = {
            "model_name": "균열 성장 예측 (GBR) + 활성 분류 (RF)",
            "growth_r2": round(r2, 4), "growth_mae": round(mae, 4),
            "active_accuracy": round(active_acc, 4), "active_f1": round(active_f1, 4),
            "feature_importance": dict(sorted(fi.items(), key=lambda x: x[1], reverse=True)),
            "future_predictions": future,
            "n_active": int(df.groupby("균열ID")["활성여부"].first().sum()),
            "n_total": df["균열ID"].nunique(),
        }
        self.results["crack"] = result
        return result

    # ════════════════════════════════════════════════════════
    # 9. 지반침하 예측 (P-051)
    # ════════════════════════════════════════════════════════
    def gen_subsidence_data(self, n_points=400):
        """지반침하 다변량 시뮬 데이터"""
        np.random.seed(self.seed + 8)
        data = []
        for i in range(n_points):
            gw_level = np.random.uniform(-5, -1) + np.random.normal(0, 0.3)
            rain_30d = np.random.exponential(80) + np.random.normal(0, 15)
            pipe_age = np.random.randint(5, 40)
            soil_perm = np.random.uniform(1e-6, 1e-3)
            insar_vel = np.random.normal(-2, 3)  # mm/year
            gpr_void_size = max(0, np.random.exponential(15))
            vibration_avg = abs(np.random.normal(0, 0.2))
            # 침하 확률 모델
            risk = (abs(gw_level + 3) * 5 + rain_30d * 0.05 + pipe_age * 0.8 +
                   np.log10(max(soil_perm, 1e-7)) * (-3) + abs(insar_vel) * 2 +
                   gpr_void_size * 0.5 + vibration_avg * 15)
            risk_norm = min(1.0, max(0.0, risk / 80))
            subsided = 1 if risk_norm > 0.5 and np.random.random() < risk_norm else 0
            data.append({
                "지점ID": f"GP-{i+1:04d}",
                "지하수위_m": round(gw_level, 2),
                "30일강수량_mm": round(rain_30d, 1),
                "관로경과년수": pipe_age,
                "투수계수": round(soil_perm, 7),
                "InSAR속도_mm년": round(insar_vel, 2),
                "GPR공동크기_cm": round(gpr_void_size, 1),
                "진동평균_g": round(vibration_avg, 4),
                "침하확률": round(risk_norm, 3),
                "침하발생": subsided,
            })
        return pd.DataFrame(data)

    def train_subsidence_model(self, df):
        """지반침하 예측 — STL-XGBoost 시뮬 (GBC)"""
        features = ["지하수위_m","30일강수량_mm","관로경과년수","투수계수","InSAR속도_mm년","GPR공동크기_cm","진동평균_g"]
        X = df[features].values
        y = df["침하발생"].values
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=self.seed, stratify=y)
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        model = GradientBoostingClassifier(n_estimators=120, max_depth=5, random_state=self.seed)
        model.fit(X_train_s, y_train)
        y_pred = model.predict(X_test_s)
        y_prob = model.predict_proba(X_test_s)[:, 1]
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        fi = dict(zip(features, model.feature_importances_))
        # 확률 회귀
        y_prob_actual = df["침하확률"].values
        Xr_tr, Xr_te, yp_tr, yp_te = train_test_split(X, y_prob_actual, test_size=0.2, random_state=self.seed)
        reg = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=self.seed)
        reg.fit(scaler.fit_transform(Xr_tr), yp_tr)
        yp_pred = reg.predict(scaler.transform(Xr_te))
        prob_r2 = r2_score(yp_te, yp_pred)
        result = {
            "model_name": "지반침하 예측 (STL-XGBoost 시뮬)",
            "accuracy": round(acc, 4), "f1_score": round(f1, 4),
            "precision": round(prec, 4), "recall": round(rec, 4),
            "prob_r2": round(prob_r2, 4),
            "feature_importance": dict(sorted(fi.items(), key=lambda x: x[1], reverse=True)),
            "subsidence_rate": round(y.mean() * 100, 1),
        }
        self.results["subsidence"] = result
        return result

    # ════════════════════════════════════════════════════════
    # 전체 파이프라인 실행
    # ════════════════════════════════════════════════════════
    def run_all(self):
        """9개 카테고리 전체 파이프라인 실행"""
        pipelines = {}

        # 1. 비전 AI
        v_data = self.gen_vision_data(500)
        v_result = self.train_vision_model(v_data)
        pipelines["vision"] = {"data": v_data, "result": v_result, "name": "🖼 비전AI 손상 분류", "category": "비전AI"}

        # 2. IoT 이상 탐지
        i_data = self.gen_iot_data(720)
        i_result = self.train_iot_anomaly_model(i_data)
        pipelines["iot"] = {"data": i_data, "result": i_result, "name": "📡 IoT 이상 탐지", "category": "IoT"}

        # 3. 민원 분류
        c_data = self.gen_complaint_data(500)
        c_result = self.train_complaint_model(c_data)
        pipelines["complaint"] = {"data": c_data, "result": c_result, "name": "📋 민원 자동 분류", "category": "민원"}

        # 4. 위험도 스코어링
        r_data = self.gen_risk_data(300)
        r_result = self.train_risk_model(r_data)
        pipelines["risk"] = {"data": r_data, "result": r_result, "name": "🔰 XAI 위험도 스코어링", "category": "위험도"}

        # 5. 고장 예측
        f_data = self.gen_failure_data(36)
        f_result = self.train_failure_model(f_data)
        pipelines["failure"] = {"data": f_data, "result": f_result, "name": "⚙ 고장 예측", "category": "고장예측"}

        # 6. 에너지 최적화
        e_data = self.gen_energy_data(365)
        e_result = self.train_energy_model(e_data)
        pipelines["energy"] = {"data": e_data, "result": e_result, "name": "⚡ 에너지 최적화", "category": "에너지"}

        # 7. 관리비 이상 탐지
        b_data = self.gen_billing_data(1000)
        b_result = self.train_billing_model(b_data)
        pipelines["billing"] = {"data": b_data, "result": b_result, "name": "🤖 관리비 이상 탐지", "category": "RPA"}

        # 8. 균열 성장 예측
        cr_data = self.gen_crack_growth_data(50, 12)
        cr_result = self.train_crack_model(cr_data)
        pipelines["crack"] = {"data": cr_data, "result": cr_result, "name": "🛡 균열 성장 예측", "category": "선제탐지"}

        # 9. 지반침하 예측
        s_data = self.gen_subsidence_data(400)
        s_result = self.train_subsidence_model(s_data)
        pipelines["subsidence"] = {"data": s_data, "result": s_result, "name": "🏗 지반침하 예측", "category": "지반침하"}

        self.pipelines = pipelines
        return pipelines

    def get_summary_table(self):
        """전체 파이프라인 성능 요약 테이블"""
        rows = []
        for key, p in self.pipelines.items():
            r = p["result"]
            if "accuracy" in r:
                metric = f"Accuracy: {r['accuracy']}"
            elif "classification_accuracy" in r:
                metric = f"Acc: {r['classification_accuracy']}, R²: {r.get('regression_r2', '-')}"
            elif "r2_score" in r:
                metric = f"R²: {r['r2_score']}, MAE: {r.get('mae', '-')}"
            elif "anomaly_accuracy" in r:
                metric = f"이상탐지 Acc: {r['anomaly_accuracy']}"
            elif "growth_r2" in r:
                metric = f"성장 R²: {r['growth_r2']}, 활성 F1: {r['active_f1']}"
            else:
                metric = str(list(r.keys())[:3])
            rows.append({
                "파이프라인": p["name"],
                "카테고리": p["category"],
                "모델": r["model_name"],
                "핵심 성능": metric,
                "데이터 수": len(p["data"]),
            })
        return pd.DataFrame(rows)

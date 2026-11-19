"""
페이지 검사 · page check (v2.5)
10개 페이지 × KR/EN 을 Streamlit AppTest 로 렌더하고
(1) 예외 (2) x · y 축 제목이 없는 차트 (3) EN 화면 차트 축에 남은 한글 을 센다.

실행 · run:  python tests/check_pages.py
"""
import json
import os
import re
import sys

from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from ui_common import PAGES  # noqa: E402

NO_AXES = {"pie", "indicator", "scatterpolar", "barpolar", "sunburst", "treemap", "table", "funnelarea"}
HANGUL = re.compile(r"[가-힣]")


def axis_titles(spec):
    lay = spec.get("layout", {})
    out = []
    for tr in spec.get("data", []):
        if tr.get("type", "scatter") in NO_AXES:
            continue
        for k in ("xaxis", "yaxis"):
            ref = tr.get(k, k[0])
            name = k + ref[1:]
            ax = lay.get(name, {})
            t = ax.get("title", {})
            t = t.get("text") if isinstance(t, dict) else t
            out.append((name, t, ax.get("visible", True)))
    return sorted(set(out), key=str)


def main():
    bad = 0
    for lang in ("ko", "en"):
        for key, en in PAGES:
            at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=600)
            at.session_state["lang"] = lang
            at.session_state["nav"] = key
            at.run()
            label = en if lang == "en" else key
            if at.exception:
                bad += 1
                print(f"[{lang}] {label}: EXCEPTION {at.exception[0].message[:300]}")
                continue
            charts = at.get("plotly_chart")
            miss, kor = [], []
            for i, c in enumerate(charts):
                spec = json.loads(c.proto.spec)
                title = (spec.get("layout", {}).get("title", {}) or {}).get("text", "") or ""
                for name, t, vis in axis_titles(spec):
                    if vis is False:
                        continue
                    if not t:
                        miss.append(f"#{i} {name} '{title[:30]}'")
                    elif lang == "en" and HANGUL.search(t):
                        kor.append(f"#{i} {name}='{t[:30]}'")
            bad += len(miss) + len(kor)
            print(f"[{lang}] {label}: charts={len(charts)} missing={len(miss)} hangul_en={len(kor)}")
            for m in miss:
                print("     missing", m)
            for k in kor:
                print("     hangul ", k)
    print("TOTAL problems:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

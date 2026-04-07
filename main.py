"""
[국토교통 AX-SPRINT] AI 기반 공공주택 안전관리 플랫폼
에이톰엔지니어링 × 세종대학교 × 한국화재보험협회

실행 진입점 (Entry Point)
  python main.py
"""

import subprocess
import sys
import os


def main():
    # app.py 경로 (같은 폴더)
    app_path = os.path.join(os.path.dirname(__file__), "app.py")

    print("=" * 60)
    print(" 에이톰-AX | AI 기반 공공주택 안전관리 플랫폼")
    print(" 국토교통부 AX-SPRINT 과제 프로토타입")
    print("=" * 60)
    print()
    print("▶ 웹 브라우저가 자동으로 열립니다.")
    print("  수동 접속: http://localhost:8501")
    print("  종료: Ctrl + C")
    print()

    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", app_path,
         "--server.headless", "false",
         "--browser.gatherUsageStats", "false"],
        check=True,
    )


if __name__ == "__main__":
    main()

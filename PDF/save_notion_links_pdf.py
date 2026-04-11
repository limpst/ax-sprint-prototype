import sys
sys.stdout.reconfigure(encoding='utf-8')

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# 한글 폰트 등록
font_paths = [
    "C:/Windows/Fonts/malgun.ttf",
    "C:/Windows/Fonts/gulim.ttc",
    "C:/Windows/Fonts/batang.ttc",
]
font_registered = False
for fp in font_paths:
    if os.path.exists(fp):
        try:
            pdfmetrics.registerFont(TTFont("Korean", fp))
            font_registered = True
            print(f"폰트 등록: {fp}")
            break
        except Exception as e:
            continue

if not font_registered:
    print("한글 폰트 없음 — 영문 폰트로 대체")
    FONT = "Helvetica"
else:
    FONT = "Korean"

OUTPUT = "notion_links.pdf"

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=A4,
    leftMargin=25*mm, rightMargin=25*mm,
    topMargin=30*mm, bottomMargin=25*mm
)

styles = getSampleStyleSheet()
title_style = ParagraphStyle("title", fontName=FONT, fontSize=16, leading=22, spaceAfter=6)
sub_style  = ParagraphStyle("sub",   fontName=FONT, fontSize=10, leading=15, spaceAfter=4, textColor=colors.grey)
body_style = ParagraphStyle("body",  fontName=FONT, fontSize=11, leading=18, spaceAfter=4)
label_style = ParagraphStyle("label",fontName=FONT, fontSize=12, leading=18, spaceAfter=6, textColor=colors.HexColor("#1a1a2e"))
url_style  = ParagraphStyle("url",   fontName=FONT, fontSize=10, leading=16, textColor=colors.HexColor("#0055cc"))

story = []

# 제목
story.append(Paragraph("에이톰-AX 사업계획서 — Notion 페이지 링크", title_style))
story.append(Paragraph("과제명: AX 기반 공공임대주택 시설물 안전·유지관리 최적화 및 지능형 행정 자동화 솔루션 상용화", sub_style))
story.append(Paragraph("저장일: 2026-04-11", sub_style))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
story.append(Spacer(1, 8*mm))

# 링크 테이블
data = [
    [Paragraph("페이지", ParagraphStyle("h", fontName=FONT, fontSize=11, textColor=colors.white)),
     Paragraph("Notion URL", ParagraphStyle("h", fontName=FONT, fontSize=11, textColor=colors.white))],
    [Paragraph("완성본 (3장+4장 전체)", body_style),
     Paragraph("https://www.notion.so/cryptolifeblck/AX-3-4-v1-33f6585be6ea80c7b9c4de02af158bc7", url_style)],
    [Paragraph("메인 페이지 (3장·4장, Claude 생성)", body_style),
     Paragraph("https://www.notion.so/33f549e480408108acdfccb31afb9098", url_style)],
    [Paragraph("제3장. 상용화 대상 제품·서비스의 개요", body_style),
     Paragraph("https://www.notion.so/33f549e4804081d8a945f5d14e9c4b5f", url_style)],
    [Paragraph("제4장. 추진전략 및 계획", body_style),
     Paragraph("https://www.notion.so/33f549e4804081fa8397c76309a6277a", url_style)],
]

table = Table(data, colWidths=[60*mm, 110*mm])
table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1a1a2e")),
    ("FONTNAME",   (0,0), (-1,-1), FONT),
    ("FONTSIZE",   (0,0), (-1,-1), 10),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f5f7ff")]),
    ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
    ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ("LEFTPADDING",   (0,0), (-1,-1), 8),
]))
story.append(table)
story.append(Spacer(1, 10*mm))

# 직접 링크 섹션
story.append(Paragraph("직접 링크", label_style))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
story.append(Spacer(1, 4*mm))

links = [
    ("완성본", "https://www.notion.so/cryptolifeblck/AX-3-4-v1-33f6585be6ea80c7b9c4de02af158bc7"),
    ("메인", "https://www.notion.so/33f549e480408108acdfccb31afb9098"),
    ("3장", "https://www.notion.so/33f549e4804081d8a945f5d14e9c4b5f"),
    ("4장", "https://www.notion.so/33f549e4804081fa8397c76309a6277a"),
]
for label, url in links:
    story.append(Paragraph(f"<b>{label}:</b>  {url}", body_style))

story.append(Spacer(1, 10*mm))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
story.append(Spacer(1, 3*mm))
story.append(Paragraph("원본 파일: 사업계획서_3장_4장_완성본.md", sub_style))

doc.build(story)
print(f"PDF 저장 완료: {OUTPUT}")

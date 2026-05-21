from io import BytesIO
from datetime import datetime, timezone, timedelta

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

JST = timezone(timedelta(hours=9))

# 日本語フォント（reportlab 内蔵 CIDFont、追加ファイル不要）
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
FONT = "HeiseiKakuGo-W5"


def _to_jst(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(JST)


def _end_time_str(start_dt: datetime, end_dt: datetime) -> str:
    """日またぎの場合、終了「時間 + 24×日数差」で表現する。
    例: 23:00 -> 翌 02:30 => "26:30"
    """
    s = _to_jst(start_dt)
    e = _to_jst(end_dt)
    day_diff = (e.date() - s.date()).days
    hour = e.hour + day_diff * 24
    return f"{hour:02d}:{e.minute:02d}"


def _para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(str(text), style)


def generate_pdf(
    records: list[dict],
    year: int,
    month: int,
    user_email: str = "",
) -> bytes:
    """作業記録 PDF を生成してバイト列で返す。

    Args:
        records: work_logs レコードのリスト。start_time / end_time は datetime 型。
        year: 対象年
        month: 対象月
        user_email: PDF に表示するユーザーメールアドレス（任意）
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    title_style = ParagraphStyle(
        "Title", fontName=FONT, fontSize=16, leading=22, spaceAfter=4
    )
    sub_style = ParagraphStyle(
        "Sub", fontName=FONT, fontSize=10, leading=14, spaceAfter=10,
        textColor=colors.HexColor("#64748B"),
    )
    cell_style = ParagraphStyle(
        "Cell", fontName=FONT, fontSize=9, leading=13
    )
    hdr_style = ParagraphStyle(
        "Hdr", fontName=FONT, fontSize=9, leading=13, textColor=colors.white
    )
    summary_style = ParagraphStyle(
        "Summary", fontName=FONT, fontSize=11, leading=16, spaceAfter=8,
        textColor=colors.HexColor("#1E293B"),
    )

    elements: list = []

    # ---- タイトル ----
    elements.append(_para(f"{year}年{month}月 作業記録レポート", title_style))
    if user_email:
        elements.append(_para(user_email, sub_style))
    elements.append(Spacer(1, 2 * mm))

    # ---- 合計作業時間 ----
    total_min = 0
    for rec in records:
        if rec.get("end_time"):
            s = _to_jst(rec["start_time"])
            e = _to_jst(rec["end_time"])
            total_min += int((e - s).total_seconds() / 60)
    total_h, total_m = divmod(total_min, 60)
    elements.append(_para(f"合計作業時間: {total_h}時間{total_m}分 （{len(records)}件）", summary_style))
    elements.append(Spacer(1, 3 * mm))

    # ---- テーブル ----
    headers = ["日付", "開始", "終了", "相手先", "作業内容", "作業時間"]
    table_data = [[_para(h, hdr_style) for h in headers]]

    for rec in records:
        start_jst = _to_jst(rec["start_time"])
        start_str = start_jst.strftime("%H:%M")
        date_str = start_jst.strftime("%Y/%m/%d")

        if rec.get("end_time"):
            end_jst = _to_jst(rec["end_time"])
            end_str = _end_time_str(rec["start_time"], rec["end_time"])
            dur_min = int((end_jst - start_jst).total_seconds() / 60)
            dur_h, dur_m = divmod(dur_min, 60)
            dur_str = f"{dur_h}h{dur_m:02d}m"
        else:
            end_str = dur_str = "—"

        table_data.append([
            _para(date_str, cell_style),
            _para(start_str, cell_style),
            _para(end_str, cell_style),
            _para(rec.get("client") or "—", cell_style),
            _para(rec.get("task_detail") or "—", cell_style),
            _para(dur_str, cell_style),
        ])

    col_widths = [28 * mm, 15 * mm, 15 * mm, 36 * mm, 62 * mm, 19 * mm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#2563EB")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#EFF6FF")]),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)

    # ---- フッター ----
    elements.append(Spacer(1, 6 * mm))
    generated_at = datetime.now(JST).strftime("%Y/%m/%d %H:%M")
    elements.append(_para(f"出力日時: {generated_at} JST", sub_style))

    doc.build(elements)
    return buf.getvalue()

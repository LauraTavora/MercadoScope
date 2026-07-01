from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.analysis import analyze_products


def _money(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_pdf_report(query: str, products: list[dict], destination: Path, version: str) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    analysis = analyze_products(products)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom", parent=styles["Title"], alignment=TA_CENTER, fontSize=20, leading=24
    )
    small = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8, leading=10)
    doc = SimpleDocTemplate(
        str(destination), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=15 * mm
    )
    story = [
        Paragraph("MercadoScope", title_style),
        Paragraph(f"Relatório automático de preços — {query}", styles["Heading2"]),
        Paragraph(f"Versão do sistema: {version}", small),
        Spacer(1, 8),
    ]

    metrics = [
        ["Produtos", str(analysis["count"]), "Preço médio", _money(analysis["mean"])],
        ["Mediana", _money(analysis["median"]), "Menor preço", _money(analysis["min"])],
        ["Maior preço", _money(analysis["max"]), "Desvio padrão", _money(analysis["stddev"])],
    ]
    metrics_table = Table(metrics, colWidths=[35 * mm, 35 * mm, 35 * mm, 45 * mm])
    metrics_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([metrics_table, Spacer(1, 12)])

    if analysis["best_value"]:
        best = analysis["best_value"]
        story.append(
            Paragraph(
                f"<b>Melhor custo-benefício estimado:</b> {best['title']} — {_money(best['price'])}",
                styles["BodyText"],
            )
        )
        story.append(Spacer(1, 8))

    rows = [["#", "Produto", "Preço", "Nota", "Vendas"]]
    for product in products[:25]:
        rows.append(
            [
                str(product.get("position", "")),
                Paragraph(str(product.get("title", ""))[:95], small),
                _money(float(product.get("price") or 0)),
                str(product.get("rating") or "—"),
                str(product.get("sold_quantity") or "—"),
            ]
        )
    table = Table(rows, repeatRows=1, colWidths=[10 * mm, 92 * mm, 28 * mm, 18 * mm, 22 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D1D5DB")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "Observação: os dados representam uma fotografia do momento da coleta. "
            "Preços, avaliações e vendas podem mudar; valide os dados antes de decisões comerciais.",
            small,
        )
    )
    doc.build(story)
    return destination

"""CSV- und PDF-Export von Konfigurationselementen.

Dynamische Attribute unterscheiden sich je CI-Typ, deshalb landen sie nicht
in eigenen Spalten, sondern als ein Text pro Zeile ("Feldname: Wert; ...").
"""

import csv
import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from domain.ci_status import ConfigItemStatus

COLUMNS = ["Name", "Typ", "Status", "Erstellt von", "Erstellt am", "Attribute"]


def _row_for(item) -> list[str]:
    sorted_values = sorted(item.field_values, key=lambda fv: fv.field_definition.position)
    attributes = "; ".join(f"{fv.field_definition.name}: {fv.value}" for fv in sorted_values if fv.value)
    return [
        item.name,
        item.config_item_type.name,
        ConfigItemStatus.LABELS.get(item.status, item.status),
        item.created_by.full_name,
        item.created_at.strftime("%d.%m.%Y %H:%M"),
        attributes,
    ]


def build_csv(items) -> bytes:
    buffer = io.StringIO()
    # Semikolon statt Komma: Excel (DE) trennt sonst beim Öffnen nicht in Spalten.
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(COLUMNS)
    for item in items:
        writer.writerow(_row_for(item))
    return buffer.getvalue().encode("utf-8-sig")  # BOM, damit Excel Umlaute korrekt erkennt


def build_pdf(items) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), title="Konfigurationselemente")
    styles = getSampleStyleSheet()

    generated_at = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M")
    elements = [
        Paragraph("Konfigurationselemente – CMDB-Export", styles["Title"]),
        Paragraph(f"Erstellt am {generated_at} UTC · {len(items)} Einträge", styles["Normal"]),
        Spacer(1, 0.5 * cm),
    ]

    data = [COLUMNS] + [_row_for(item) for item in items]
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f4f4")]),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)
    return buffer.getvalue()

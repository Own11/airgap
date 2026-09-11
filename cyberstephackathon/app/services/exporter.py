import csv
import io
import json
from typing import Any

from app.models.schemas import MeetingProtocol, MeetingTranscript


def export_json(transcript: MeetingTranscript | None, protocol: MeetingProtocol | None) -> bytes:
    return json.dumps({"transcript": transcript.model_dump() if transcript else None, "protocol": protocol.model_dump() if protocol else None}, ensure_ascii=False, indent=2).encode()


def export_csv(protocol: MeetingProtocol) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["type", "value", "assignee", "deadline", "priority"])
    writer.writerow(["summary", protocol.summary, "", "", ""])
    for decision in protocol.decisions:
        writer.writerow(["decision", decision, "", "", ""])
    for item in protocol.action_items:
        writer.writerow(["action_item", item.task, item.assignee or "", item.deadline or "", item.priority])
    return output.getvalue().encode("utf-8-sig")


def export_pdf(protocol: MeetingProtocol) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    output = io.BytesIO()
    document = canvas.Canvas(output, pagesize=A4)
    _, height = A4
    y = height - 55
    document.setFont("Helvetica-Bold", 18)
    document.drawString(45, y, "AirGap — Meeting Protocol")
    y -= 35
    document.setFont("Helvetica", 11)
    for title, values in (("Summary", [protocol.summary]), ("Decisions", protocol.decisions), ("Topics", protocol.topics), ("Open questions", protocol.open_questions), ("Risks", protocol.risks)):
        document.setFont("Helvetica-Bold", 12)
        document.drawString(45, y, title)
        y -= 18
        document.setFont("Helvetica", 10)
        for value in values:
            document.drawString(58, y, f"• {value[:105]}")
            y -= 15
            if y < 55:
                document.showPage()
                y = height - 55
        y -= 10
    document.save()
    return output.getvalue()

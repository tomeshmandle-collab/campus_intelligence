"""
Generator for benchmark college notice sample PDFs in pure Python (zero external dependencies).
Creates valid PDF 1.4 documents for testing the CAI Campus Intelligence pipeline.
"""

import json
from pathlib import Path


def generate_pdf_bytes(title: str, notice_date: str, deadline: str | None, audience: str, category: str, page_count: int, is_scanned: bool, notes: str) -> bytes:
    """
    Generates a valid, readable PDF-1.4 file with text content for testing.
    """
    objects = []
    
    # Object 1: Catalog
    # Object 2: Pages root
    # Object 3..3+(page_count-1): Page objects
    # Object 3+page_count..: Content streams
    # Font Object
    
    page_obj_ids = [3 + i for i in range(page_count)]
    content_obj_ids = [3 + page_count + i for i in range(page_count)]
    font_obj_id = 3 + 2 * page_count
    
    # Obj 1: Catalog
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    
    # Obj 2: Pages
    kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    objects.append(f"2 0 obj\n<< /Type /Pages /Kids [{kids_str}] /Count {page_count} >>\nendobj\n".encode("latin1"))
    
    # Obj 3..Pages
    for i, (p_id, c_id) in enumerate(zip(page_obj_ids, content_obj_ids)):
        page_dict = (
            f"{p_id} 0 obj\n"
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {c_id} 0 R "
            f"/Resources << /Font << /F1 {font_obj_id} 0 R >> >> >>\n"
            f"endobj\n"
        )
        objects.append(page_dict.encode("latin1"))
        
    # Obj Content streams
    for page_idx in range(page_count):
        c_id = content_obj_ids[page_idx]
        lines = [
            "KIRORI MAL COLLEGE (UNIVERSITY OF DELHI)",
            "CENTRE FOR ARTIFICIAL INTELLIGENCE & CAMPUS INTELLIGENCE",
            f"NOTICE / CIRCULAR: {category.upper()}",
            "--------------------------------------------------------------------------------",
            f"DATE OF NOTICE: {notice_date}",
            f"AUDIENCE: {audience.upper()}",
            f"DEADLINE: {deadline if deadline else 'N/A'}",
            f"PAGE: {page_idx + 1} of {page_count}",
            "",
            f"SUBJECT: {title}",
            "",
        ]
        if page_idx == 0:
            lines.extend([
                "This is an official administrative notice issued for public college record.",
                f"Notes: {notes}",
                "All concerned students and staff are requested to adhere to the given schedule.",
            ])
            if deadline:
                lines.append(f"CRITICAL DATE: Applications/submissions close strictly on {deadline}.")
        else:
            lines.extend([
                f"Continuation Sheet - Page {page_idx + 1}",
                "Detailed breakdown, procedural instructions, and schedule tables:",
                "- Schedule Item A: Detailed requirements and verification",
                "- Schedule Item B: Submission counter and contact desks",
                "- Schedule Item C: Applicable policies and regulatory compliances",
            ])
            
        # Format lines for PDF text stream
        text_ops = [
            "BT",
            "/F1 12 Tf",
            "50 740 Td",
            "18 TL",
        ]
        for line in lines:
            # Escape parenthesis
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            text_ops.append(f"({escaped}) Tj")
            text_ops.append("T*")
        text_ops.append("ET")
        
        stream_data = "\n".join(text_ops).encode("latin1")
        stream_obj = (
            f"{c_id} 0 obj\n"
            f"<< /Length {len(stream_data)} >>\n"
            f"stream\n"
        ).encode("latin1") + stream_data + b"\nendstream\nendobj\n"
        objects.append(stream_obj)
        
    # Font Object
    font_obj = (
        f"{font_obj_id} 0 obj\n"
        f"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n"
        f"endobj\n"
    ).encode("latin1")
    objects.append(font_obj)
    
    # Build complete PDF with xref
    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    body = bytearray(header)
    offsets = []
    
    for obj in objects:
        offsets.append(len(body))
        body.extend(obj)
        
    xref_offset = len(body)
    total_objects = len(objects) + 1
    
    xref = [
        f"xref\n0 {total_objects}\n",
        "0000000000 65535 f \n",
    ]
    for off in offsets:
        xref.append(f"{off:010d} 00000 n \n")
        
    trailer = (
        f"trailer\n"
        f"<< /Size {total_objects} /Root 1 0 R >>\n"
        f"startxref\n"
        f"{xref_offset}\n"
        f"%%EOF\n"
    )
    
    body.extend("".join(xref).encode("latin1"))
    body.extend(trailer.encode("latin1"))
    return bytes(body)


def main():
    script_dir = Path(__file__).resolve().parent
    fixtures_dir = script_dir.parent / "fixtures" / "sample_notices"
    manifest_path = fixtures_dir / "manifest.json"
    
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    print(f"Generating {len(manifest)} sample PDF files in {fixtures_dir}...")
    for item in manifest:
        pdf_path = fixtures_dir / item["filename"]
        pdf_bytes = generate_pdf_bytes(
            title=item["expected_title"],
            notice_date=item["expected_notice_date"],
            deadline=item.get("expected_deadline_date"),
            audience=item["expected_audience"],
            category=item.get("expected_category", "General"),
            page_count=item.get("page_count", 1),
            is_scanned=item.get("is_scanned", False),
            notes=item.get("edge_case_notes", ""),
        )
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"  [+] Created: {item['filename']} ({len(pdf_bytes)} bytes, {item['page_count']} page(s))")

    print("\n[SUCCESS] All sample PDFs generated.")


if __name__ == "__main__":
    main()

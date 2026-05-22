"""
Minimal pure-Python PDF writer (no dependencies).
Supports: text, bold, line breaks, multiple pages, Helvetica / Helvetica-Bold.
"""

from __future__ import annotations
import io
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class _Page:
    ops: List[str] = field(default_factory=list)  # PDF stream operators

    def add_op(self, op: str):
        self.ops.append(op)


class PDF:
    """Write a simple multi-page PDF with plain and bold text."""

    PAGE_W = 612   # US Letter, points
    PAGE_H = 792

    def __init__(self):
        self._pages: List[_Page] = []
        self._cur: _Page | None = None
        self.new_page()

    def new_page(self):
        self._cur = _Page()
        self._pages.append(self._cur)

    def _esc(self, text: str) -> str:
        """Escape special PDF string characters and strip non-latin-1 chars."""
        text = text.replace("—", "-").replace("–", "-").replace("’", "'").replace("“", '"').replace("”", '"')
        text = text.encode("latin-1", errors="replace").decode("latin-1")
        return (text
                .replace("\\", "\\\\")
                .replace("(", "\\(")
                .replace(")", "\\)")
                .replace("\r", "\\r")
                .replace("\n", "\\n"))

    def text(self, x: float, y: float, content: str, size: int = 10, bold: bool = False):
        """Place a single line of text at (x, y) from top-left."""
        pdf_y = self.PAGE_H - y  # flip to bottom-origin
        font = "F2" if bold else "F1"
        op = (
            f"BT /{font} {size} Tf {x:.1f} {pdf_y:.1f} Td "
            f"({self._esc(content)}) Tj ET"
        )
        self._cur.add_op(op)

    def hline(self, x1: float, y: float, x2: float):
        """Draw a horizontal line."""
        pdf_y = self.PAGE_H - y
        self._cur.add_op(f"{x1:.1f} {pdf_y:.1f} m {x2:.1f} {pdf_y:.1f} l S")

    def rect(self, x: float, y: float, w: float, h: float, fill: bool = False):
        """Draw a rectangle (top-left origin)."""
        pdf_y = self.PAGE_H - y
        op = f"{x:.1f} {pdf_y - h:.1f} {w:.1f} {h:.1f} re " + ("f" if fill else "S")
        self._cur.add_op(op)

    def paragraph(self, x: float, y_start: float, lines: List[str],
                  size: int = 10, bold: bool = False, leading: int = 14) -> float:
        """Place a list of lines; return the y after the last line."""
        y = y_start
        for line in lines:
            if line:
                self.text(x, y, line, size=size, bold=bold)
            y += leading
        return y

    def write(self, path: str):
        buf = io.BytesIO()

        def w(s: str):
            buf.write((s + "\n").encode("latin-1"))

        offsets: List[int] = []

        # Header
        w("%PDF-1.4")

        # Font resources are shared; we embed them in each page for simplicity
        font1_id = 1
        font2_id = 2
        first_page_obj = 3

        # Object 1: Helvetica
        offsets.append(buf.tell())
        w("1 0 obj")
        w("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        w("endobj")

        # Object 2: Helvetica-Bold
        offsets.append(buf.tell())
        w("2 0 obj")
        w("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        w("endobj")

        # One content stream + one page object per page
        page_obj_ids: List[int] = []
        next_id = first_page_obj

        for page in self._pages:
            stream_content = "\n".join(page.ops)
            stream_bytes = stream_content.encode("latin-1")

            # Content stream object
            offsets.append(buf.tell())
            w(f"{next_id} 0 obj")
            w(f"<< /Length {len(stream_bytes)} >>")
            w("stream")
            buf.write(stream_bytes)
            buf.write(b"\n")
            w("endstream")
            w("endobj")
            stream_id = next_id
            next_id += 1

            # Page object
            offsets.append(buf.tell())
            w(f"{next_id} 0 obj")
            w("<< /Type /Page /Parent 999 0 R")
            w(f"   /MediaBox [0 0 {self.PAGE_W} {self.PAGE_H}]")
            w("   /Resources << /Font << /F1 1 0 R /F2 2 0 R >> >>")
            w(f"   /Contents {stream_id} 0 R >>")
            w("endobj")
            page_obj_ids.append(next_id)
            next_id += 1

        # Pages object
        pages_id = next_id
        offsets.append(buf.tell())
        kids = " ".join(f"{i} 0 R" for i in page_obj_ids)
        w(f"{pages_id} 0 obj")
        w(f"<< /Type /Pages /Kids [{kids}] /Count {len(self._pages)} >>")
        w("endobj")
        next_id += 1

        # Catalog — we promised 999 for /Parent; re-number properly
        # Rebuild with correct pages_id as /Parent in all page objects
        # Simpler: just write a catalog pointing to pages_id and trust the reader
        catalog_id = next_id
        offsets.append(buf.tell())
        w(f"{catalog_id} 0 obj")
        w(f"<< /Type /Catalog /Pages {pages_id} 0 R >>")
        w("endobj")

        # Now patch page objects to use correct pages_id instead of 999
        # We need to rewrite the buffer — easier: use a second pass approach
        # For simplicity just write a placeholder-free version:
        pass  # handled below via rebuild

        xref_offset = buf.tell()

        # xref — count is catalog_id + 1 (objects 0..catalog_id)
        total_objs = catalog_id + 1
        # Recount: obj IDs are 1,2, then first_page_obj through catalog_id
        all_ids = [1, 2] + list(range(first_page_obj, catalog_id + 1))

        # Build proper xref by rewinding and rebuilding
        # This minimal impl just records buf positions for each object
        # We already have offsets[] in order of writing: font1, font2, then pairs of (stream,page) per page, pages, catalog
        # Map object id → offset
        id_to_offset: dict[int, int] = {}
        id_to_offset[1] = offsets[0]
        id_to_offset[2] = offsets[1]
        idx = 2
        page_obj_start = first_page_obj
        for i in range(len(self._pages)):
            id_to_offset[page_obj_start + i * 2] = offsets[idx]      # stream
            id_to_offset[page_obj_start + i * 2 + 1] = offsets[idx + 1]  # page
            idx += 2
        id_to_offset[pages_id] = offsets[idx]
        id_to_offset[catalog_id] = offsets[idx + 1]

        # xref table — sequential from 0 to max_id
        max_id = catalog_id
        w(f"xref\n0 {max_id + 1}")
        w("0000000000 65535 f ")
        for oid in range(1, max_id + 1):
            off = id_to_offset.get(oid, 0)
            if off:
                w(f"{off:010d} 00000 n ")
            else:
                # Patch /Parent 999 → correct pages_id inline won't work, so
                # for page objects that reference /Parent 999 0 R we emit a dummy entry
                w(f"0000000000 65535 f ")

        w(f"trailer\n<< /Size {max_id + 1} /Root {catalog_id} 0 R >>")
        w(f"startxref\n{xref_offset}")
        w("%%EOF")

        # Now actually write — but we have the /Parent 999 problem.
        # Rewrite the whole thing with the correct pages_id substituted.
        raw = buf.getvalue().decode("latin-1")
        raw = raw.replace("/Parent 999 0 R", f"/Parent {pages_id} 0 R")

        with open(path, "wb") as f:
            f.write(raw.encode("latin-1"))

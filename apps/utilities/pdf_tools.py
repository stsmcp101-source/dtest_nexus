"""
Pure PDF-manipulation helpers behind the PDF Edit tool (merge / split /
delete pages / insert / lock / unlock). Every function takes already-
validated Django UploadedFile objects and returns an in-memory
io.BytesIO — nothing here touches request/response objects or the
filesystem, so the view layer stays a thin adapter and these are easy
to reason about in isolation.
"""
import io
import zipfile

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError


class ToolError(Exception):
    """Raised with a Thai, user-facing message on any bad input or
    unreadable PDF — caught in the view and shown to the user."""


def _read_pdf(uploaded_file, label="ไฟล์ PDF"):
    try:
        reader = PdfReader(uploaded_file)
        if reader.is_encrypted:
            raise ToolError(f"{label} มีการเข้ารหัสอยู่แล้ว กรุณาปลดรหัสก่อน (ใช้แท็บ ล็อก/ปลดล็อก) แล้วค่อยนำมาใช้กับเครื่องมือนี้")
        # Touch page count now so a corrupt file fails here, not later
        # mid-operation.
        _ = len(reader.pages)
        return reader
    except ToolError:
        raise
    except (PdfReadError, ValueError, KeyError) as exc:
        raise ToolError(f"ไม่สามารถอ่าน {label} ได้ — ไฟล์อาจเสียหายหรือไม่ใช่ PDF ที่ถูกต้อง") from exc


def parse_page_ranges(spec, max_pages):
    """Parses a spec like '1-3,5,7-9' (1-indexed, inclusive) into a
    sorted list of unique 0-indexed page numbers, bounds-checked against
    max_pages. Raises ToolError with a Thai message on any bad input."""
    pages = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            parts = chunk.split("-")
            if len(parts) != 2 or not all(p.strip().isdigit() for p in parts):
                raise ToolError(f"รูปแบบช่วงหน้าไม่ถูกต้อง: '{chunk}'")
            start, end = int(parts[0]), int(parts[1])
        elif chunk.isdigit():
            start = end = int(chunk)
        else:
            raise ToolError(f"รูปแบบช่วงหน้าไม่ถูกต้อง: '{chunk}'")

        if start < 1 or end < start or end > max_pages:
            raise ToolError(f"ช่วงหน้า '{chunk}' อยู่นอกขอบเขตของเอกสาร ({max_pages} หน้า)")
        pages.update(range(start - 1, end))

    if not pages:
        raise ToolError("กรุณาระบุช่วงหน้าอย่างน้อยหนึ่งช่วง")
    return sorted(pages)


def get_page_count(uploaded_file):
    """Reads just the page count of an (unencrypted) PDF — used to
    populate the page-picker list in the Split / Delete Pages tabs
    before the user commits to an operation."""
    reader = _read_pdf(uploaded_file)
    return len(reader.pages)


def merge_pdfs(uploaded_files):
    if len(uploaded_files) < 2:
        raise ToolError("กรุณาเลือกไฟล์ PDF อย่างน้อย 2 ไฟล์เพื่อรวม")

    writer = PdfWriter()
    for f in uploaded_files:
        reader = _read_pdf(f, label=f"ไฟล์ '{f.name}'")
        for page in reader.pages:
            writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output


def split_pdf(uploaded_file, ranges_spec="", chunk_size=None):
    """Returns a ZIP of PDFs.
    - chunk_size set: groups pages into consecutive chunks of that size
      (e.g. 10 pages, chunk_size=3 -> 1-3, 4-6, 7-9, 10).
    - ranges_spec set (and no chunk_size): one PDF per comma-separated
      group (e.g. '1-3,4-6' or a plain page list like '2,5,7' for
      "selected pages, one file each").
    - neither set: splits every page into its own single-page PDF.
    """
    reader = _read_pdf(uploaded_file)
    total = len(reader.pages)

    if chunk_size:
        if chunk_size < 1:
            raise ToolError("จำนวนหน้าต่อไฟล์ต้องมากกว่า 0")
        groups = [list(range(i, min(i + chunk_size, total))) for i in range(0, total, chunk_size)]
    elif ranges_spec.strip():
        groups = [parse_page_ranges(chunk, total) for chunk in ranges_spec.split(",")]
    else:
        groups = [[i] for i in range(total)]

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, page_indexes in enumerate(groups, start=1):
            writer = PdfWriter()
            for idx in page_indexes:
                writer.add_page(reader.pages[idx])
            part = io.BytesIO()
            writer.write(part)
            zf.writestr(f"split_{i}.pdf", part.getvalue())
    zip_buffer.seek(0)
    return zip_buffer


def extract_pages(uploaded_file, pages_spec):
    """Returns a single PDF containing only the given pages (ascending
    order) — used by Split's "selected pages, combined into one file"
    mode."""
    reader = _read_pdf(uploaded_file)
    total = len(reader.pages)
    indexes = parse_page_ranges(pages_spec, total)

    writer = PdfWriter()
    for idx in indexes:
        writer.add_page(reader.pages[idx])

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output


def delete_pages(uploaded_file, pages_spec):
    reader = _read_pdf(uploaded_file)
    total = len(reader.pages)
    to_remove = set(parse_page_ranges(pages_spec, total))
    if len(to_remove) >= total:
        raise ToolError("ไม่สามารถลบทุกหน้าออกจากเอกสารได้ ต้องเหลืออย่างน้อย 1 หน้า")

    writer = PdfWriter()
    for idx, page in enumerate(reader.pages):
        if idx not in to_remove:
            writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output


def insert_pdf(base_file, insert_files, mode="end", custom_position=0):
    """Inserts one or more files, in the given order, into base_file.
    mode is one of 'start', 'end', 'custom' (insert after page
    custom_position, 0 = before the first page)."""
    if not insert_files:
        raise ToolError("กรุณาเลือกไฟล์ที่จะแทรกอย่างน้อย 1 ไฟล์")

    base_reader = _read_pdf(base_file, label="ไฟล์หลัก")
    base_total = len(base_reader.pages)

    if mode == "start":
        position = 0
    elif mode == "end":
        position = base_total
    else:
        position = custom_position
        if position < 0 or position > base_total:
            raise ToolError(f"ตำแหน่งแทรกต้องอยู่ระหว่าง 0 ถึง {base_total}")

    writer = PdfWriter()
    for page in base_reader.pages[:position]:
        writer.add_page(page)
    for f in insert_files:
        reader = _read_pdf(f, label=f"ไฟล์ที่จะแทรก '{f.name}'")
        for page in reader.pages:
            writer.add_page(page)
    for page in base_reader.pages[position:]:
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output


def encrypt_pdf(uploaded_file, password, owner_password=""):
    if not password or len(password) < 4:
        raise ToolError("กรุณาตั้งรหัสผ่านสำหรับเปิดไฟล์อย่างน้อย 4 ตัวอักษร")

    reader = _read_pdf(uploaded_file)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(user_password=password, owner_password=owner_password or None)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output


def decrypt_pdf(uploaded_file, password):
    if not password:
        raise ToolError("กรุณาระบุรหัสผ่านปัจจุบันของไฟล์")

    try:
        reader = PdfReader(uploaded_file)
    except (PdfReadError, ValueError, KeyError) as exc:
        raise ToolError("ไม่สามารถอ่านไฟล์ PDF ได้ — ไฟล์อาจเสียหายหรือไม่ใช่ PDF ที่ถูกต้อง") from exc

    if not reader.is_encrypted:
        raise ToolError("ไฟล์นี้ไม่ได้ถูกล็อกด้วยรหัสผ่าน")

    try:
        result = reader.decrypt(password)
    except Exception as exc:  # pypdf raises assorted crypto errors on bad input
        raise ToolError("ไม่สามารถปลดล็อกไฟล์ได้ — เกิดข้อผิดพลาดขณะถอดรหัส") from exc
    if not result:
        raise ToolError("รหัสผ่านไม่ถูกต้อง")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output

"""
Document Converter helpers.

- images_to_pdf / pdf_to_images: pure Python (Pillow + PyMuPDF), no
  external app required, safe to run on any platform.
- office_to_pdf: there is no pure-Python library that renders
  .docx/.xlsx to PDF with real fidelity, so this drives the actual
  desktop Word/Excel application through COM automation (win32com).
  That means it only works on Windows, only when Microsoft Word/Excel
  is installed on whatever machine runs the Django process, and calls
  must be serialized (COM Application objects aren't safe to drive
  from two request threads at once) — see _office_com_lock below.
"""
import io
import os
import tempfile
import threading
import zipfile

import pymupdf
from PIL import Image, UnidentifiedImageError

from .pdf_tools import ToolError

_office_com_lock = threading.Lock()

OFFICE_WORD_EXTENSIONS = {".doc", ".docx"}
OFFICE_EXCEL_EXTENSIONS = {".xls", ".xlsx"}


def images_to_pdf(uploaded_files):
    if not uploaded_files:
        raise ToolError("กรุณาเลือกไฟล์รูปภาพอย่างน้อย 1 ไฟล์")

    pages = []
    for f in uploaded_files:
        try:
            img = Image.open(f)
            img.load()
        except UnidentifiedImageError as exc:
            raise ToolError(f"'{f.name}' ไม่ใช่ไฟล์รูปภาพที่รองรับ") from exc
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        pages.append(img)

    output = io.BytesIO()
    first, rest = pages[0], pages[1:]
    first.save(output, format="PDF", save_all=True, append_images=rest)
    output.seek(0)
    return output


def pdf_to_images(uploaded_file, dpi=150):
    """Rasterizes every page of a PDF to a PNG (via PyMuPDF) and returns
    them zipped — unlike pdf_tools (pypdf), this renders actual page
    content rather than just manipulating the page tree."""
    try:
        doc = pymupdf.open(stream=uploaded_file.read(), filetype="pdf")
    except Exception as exc:
        raise ToolError("ไม่สามารถอ่านไฟล์ PDF ได้ — ไฟล์อาจเสียหายหรือไม่ใช่ PDF ที่ถูกต้อง") from exc

    if doc.is_encrypted:
        doc.close()
        raise ToolError("ไฟล์ PDF นี้มีการเข้ารหัสอยู่ กรุณาปลดรหัสก่อน")
    if doc.page_count == 0:
        doc.close()
        raise ToolError("ไฟล์ PDF นี้ไม่มีหน้าเอกสาร")

    matrix = pymupdf.Matrix(dpi / 72, dpi / 72)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i in range(doc.page_count):
            pix = doc[i].get_pixmap(matrix=matrix)
            zf.writestr(f"page_{i + 1}.png", pix.tobytes("png"))
    doc.close()
    zip_buffer.seek(0)
    return zip_buffer


def office_to_pdf(uploaded_file):
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext in OFFICE_WORD_EXTENSIONS:
        app_kind = "word"
    elif ext in OFFICE_EXCEL_EXTENSIONS:
        app_kind = "excel"
    else:
        raise ToolError("รองรับเฉพาะไฟล์ .doc, .docx, .xls, .xlsx เท่านั้น")

    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        raise ToolError(
            "การแปลงไฟล์ Office ต้องใช้ Microsoft Word/Excel บนเครื่องเซิร์ฟเวอร์ (รองรับเฉพาะ Windows)"
        ) from exc

    with tempfile.TemporaryDirectory() as tmp_dir:
        src_path = os.path.join(tmp_dir, "source" + ext)
        pdf_path = os.path.join(tmp_dir, "output.pdf")
        with open(src_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        with _office_com_lock:
            pythoncom.CoInitialize()
            app = None
            try:
                if app_kind == "word":
                    app = win32com.client.DispatchEx("Word.Application")
                    app.Visible = False
                    app.DisplayAlerts = 0  # wdAlertsNone
                    doc = app.Documents.Open(src_path, ReadOnly=True)
                    doc.SaveAs(pdf_path, FileFormat=17)  # wdFormatPDF
                    doc.Close(False)
                else:
                    app = win32com.client.DispatchEx("Excel.Application")
                    app.Visible = False
                    app.DisplayAlerts = False
                    wb = app.Workbooks.Open(src_path, ReadOnly=True)
                    wb.ExportAsFixedFormat(0, pdf_path)  # xlTypePDF
                    wb.Close(False)
            except Exception as exc:
                raise ToolError(f"แปลงไฟล์ไม่สำเร็จ — โปรแกรม Office รายงานข้อผิดพลาด: {exc}") from exc
            finally:
                if app is not None:
                    try:
                        app.Quit()
                    except Exception:
                        pass
                pythoncom.CoUninitialize()

        if not os.path.exists(pdf_path):
            raise ToolError("แปลงไฟล์ไม่สำเร็จ — ไม่พบไฟล์ผลลัพธ์")
        with open(pdf_path, "rb") as f:
            output = io.BytesIO(f.read())
    output.seek(0)
    return output

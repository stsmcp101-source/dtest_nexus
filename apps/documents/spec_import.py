"""
Excel import for the equipment spec list (rule: non-technical staff
maintain this list in a spreadsheet shaped like No / Year / Indoor /
Outdoor / Report Dev / Report Sam — "No" is just a row number and is
ignored on import).
"""
import openpyxl

from .models import EquipmentSpec


class SpecImportError(Exception):
    pass


def import_equipment_specs_from_excel(file_obj, user):
    """Creates one EquipmentSpec per data row. Returns (created_count, errors)
    where errors is a list of (row_number, message) for rows that couldn't
    be imported — a bad row is skipped, not fatal to the whole import."""
    try:
        workbook = openpyxl.load_workbook(file_obj, data_only=True, read_only=True)
    except Exception as exc:
        raise SpecImportError(f"ไม่สามารถอ่านไฟล์ Excel นี้ได้: {exc}") from exc

    sheet = workbook.active
    rows = sheet.iter_rows(values_only=True)
    try:
        header_row = next(rows)
    except StopIteration:
        raise SpecImportError("ไฟล์ Excel ว่างเปล่า")

    header_index = {
        str(cell).strip().lower(): idx
        for idx, cell in enumerate(header_row)
        if cell is not None
    }

    year_col = header_index.get("year")
    indoor_col = header_index.get("indoor")
    outdoor_col = header_index.get("outdoor")
    dev_col = header_index.get("report dev")
    sam_col = header_index.get("report sam")

    if year_col is None or indoor_col is None:
        raise SpecImportError(
            "ไม่พบคอลัมน์ Year หรือ Indoor — แถวแรกของไฟล์ต้องเป็นหัวตาราง "
            "Year, Indoor, Outdoor, Report Dev, Report Sam"
        )

    def cell_text(row, col_index):
        if col_index is None or col_index >= len(row):
            return ""
        value = row[col_index]
        return "" if value is None else str(value).strip()

    created = 0
    errors = []
    for row_number, row in enumerate(rows, start=2):
        if row is None or all(cell in (None, "") for cell in row):
            continue
        year_text = cell_text(row, year_col)
        if not year_text:
            continue
        try:
            EquipmentSpec.objects.create(
                year=int(float(year_text)),
                indoor_unit=cell_text(row, indoor_col),
                outdoor_unit=cell_text(row, outdoor_col),
                report_dev_code=cell_text(row, dev_col),
                report_sam_code=cell_text(row, sam_col),
                created_by=user,
                updated_by=user,
            )
            created += 1
        except (ValueError, TypeError) as exc:
            errors.append((row_number, str(exc)))

    return created, errors

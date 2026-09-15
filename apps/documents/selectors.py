"""
Selectors: read-side queryset construction for the Document module,
kept separate from views.py per rule #31 (no heavy business logic
inline in views). Everything here operates on Django ORM querysets —
search, filter, and sort all happen in the database, never by pulling
everything into Python or JavaScript (rule #23).
"""
from django.db.models import Count, Q

from .models import Document, EquipmentSpec


def get_document_queryset(*, category_code=None, search=None, file_type=None, sort=None):
    qs = Document.objects.select_related("category", "document_type", "source", "created_by")

    if category_code and category_code != "all":
        qs = qs.filter(category__code=category_code)

    if search:
        qs = qs.filter(
            Q(document_name__icontains=search)
            | Q(document_code__icontains=search)
            | Q(category__name__icontains=search)
        )

    if file_type:
        qs = qs.filter(file_type__iexact=file_type)

    sort_map = {
        "recent": "-updated_at",
        "name": "document_name",
        "code": "document_code",
    }
    qs = qs.order_by(sort_map.get(sort, "-updated_at"))
    return qs


def get_category_counts():
    from .models import DocumentCategory

    counts = []
    total = Document.objects.count()
    counts.append({"code": "all", "name": "ทั้งหมด", "count": total})
    for category in DocumentCategory.objects.all():
        counts.append({
            "code": category.code,
            "name": category.name,
            "count": category.documents.count(),
        })
    return counts


def get_year_counts(category_code=None):
    """Document counts grouped by year (see storage.detect_document_year
    for how the year is derived), oldest first, for the year chart on
    the Document Data list page. Undated documents are excluded. Respects
    the same category filter as the table so the chart always reflects
    whatever the user has selected (all / Dev / Mass) — each row also
    carries the dev/mass split so an unfiltered chart can render a
    two-colour stacked bar per year."""
    qs = Document.objects.exclude(document_year__isnull=True)
    if category_code and category_code != "all":
        qs = qs.filter(category__code=category_code)

    rows = (
        qs.values("document_year", "category__code")
        .annotate(count=Count("id"))
        .order_by("document_year")
    )

    by_year = {}
    for row in rows:
        year = row["document_year"]
        entry = by_year.setdefault(year, {"document_year": year, "dev": 0, "mass": 0})
        entry[row["category__code"]] = row["count"]

    result = []
    for year in sorted(by_year):
        entry = by_year[year]
        entry["total"] = entry["dev"] + entry["mass"]
        result.append(entry)

    max_count = max((row["total"] for row in result), default=0)
    return result, max_count


def get_equipment_spec_queryset(search=None):
    qs = EquipmentSpec.objects.order_by("year", "id")
    if search:
        qs = qs.filter(
            Q(indoor_unit__icontains=search)
            | Q(outdoor_unit__icontains=search)
            | Q(report_dev_code__icontains=search)
            | Q(report_sam_code__icontains=search)
            | Q(year__icontains=search)
        )
    return qs

import json
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from apps.audit.services import log_action
from apps.audit.utils import get_client_ip
from apps.permissions.decorators import require_permission
from apps.permissions.registry import user_has

from .models import SparePart, SparePartTransaction

TX_LABELS = dict(SparePartTransaction.TxType.choices)


@login_required
@require_permission("internal.view")
def index(request):
    parts = SparePart.objects.all().order_by("pn")
    txlog = SparePartTransaction.objects.all()[:2000]
    categories = sorted({p.cat for p in parts if p.cat})
    subcategories = sorted({p.sub for p in parts if p.sub})
    context = {
        "can_edit": user_has(request.user, "internal.spare_part_edit"),
        "parts_data": [p.as_dict() for p in parts],
        "txlog_data": [t.as_dict() for t in txlog],
        "part_count": parts.count(),
        "categories": categories,
        "subcategories": subcategories,
    }
    return render(request, "spare_parts/index.html", context)


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_decimal(value, default=Decimal("0")):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _clean_str(value, max_len=None):
    s = str(value or "").strip()
    return s[:max_len] if max_len else s


@login_required
@require_permission("internal.spare_part_edit")
@require_POST
def api_transaction(request):
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "message": "ข้อมูลไม่ถูกต้อง"}, status=400)

    mode = data.get("mode")
    pn = _clean_str(data.get("pn"), 30).upper()
    desc = _clean_str(data.get("desc"), 200)
    qty_raw = data.get("qty")
    by = _clean_str(data.get("by"), 100) or "—"
    team = _clean_str(data.get("team"), 20)
    reason = _clean_str(data.get("reason"), 200) or "—"
    if team:
        by = f"{by} [{team}]"

    if not pn:
        return JsonResponse({"ok": False, "message": "กรุณากรอก Part Number"}, status=400)
    if mode not in dict(SparePartTransaction.TxType.choices):
        return JsonResponse({"ok": False, "message": "โหมดไม่ถูกต้อง"}, status=400)

    part = SparePart.objects.filter(pn=pn).first()

    with transaction.atomic():
        if mode == "new":
            if not desc:
                return JsonResponse({"ok": False, "message": "กรุณากรอกชื่ออะไหล่"}, status=400)
            if part:
                return JsonResponse({"ok": False, "message": "Part Number นี้มีอยู่แล้ว"}, status=400)
            qty = max(0, _to_int(qty_raw))
            part = SparePart.objects.create(
                pn=pn, desc=desc,
                cat=_clean_str(data.get("cat"), 30), sub=_clean_str(data.get("sub"), 50),
                mfr=_clean_str(data.get("mfr"), 100), model=_clean_str(data.get("model"), 150),
                unit=_clean_str(data.get("unit"), 10) or "EA",
                price=_to_decimal(data.get("price")),
                min_stock=max(0, _to_int(data.get("min"))),
                cur_stock=qty,
                location=_clean_str(data.get("loc"), 100),
                lead_time_days=_clean_str(data.get("lead"), 20) or "7",
                remarks=reason if reason != "—" else "",
            )
            tx = SparePartTransaction.objects.create(
                part=part, pn=pn, desc=desc, tx_type="new",
                delta=qty, before=0, after=qty, by=by, reason=reason,
            )
            message = f"เพิ่ม {pn} เรียบร้อย"

        elif mode == "receive":
            if not part:
                return JsonResponse({"ok": False, "message": "ไม่พบ Part Number — ใช้โหมด เพิ่มใหม่"}, status=400)
            qty = _to_int(qty_raw)
            if not qty:
                return JsonResponse({"ok": False, "message": "กรุณากรอกจำนวนที่รับ"}, status=400)
            before = part.cur_stock
            part.cur_stock = before + qty
            part.save(update_fields=["cur_stock", "updated_at"])
            tx = SparePartTransaction.objects.create(
                part=part, pn=pn, desc=f"{part.desc} {part.model}".strip(), tx_type="receive",
                delta=qty, before=before, after=part.cur_stock, by=by, reason=reason,
            )
            message = f"รับเข้า {qty} {part.unit} ({before}→{part.cur_stock})"

        elif mode == "withdraw":
            if not part:
                return JsonResponse({"ok": False, "message": "ไม่พบ Part Number"}, status=400)
            qty = _to_int(qty_raw)
            if not qty:
                return JsonResponse({"ok": False, "message": "กรุณากรอกจำนวน"}, status=400)
            if qty > part.cur_stock:
                return JsonResponse({"ok": False, "message": f"สต็อกไม่พอ (มี {part.cur_stock} {part.unit})"}, status=400)
            before = part.cur_stock
            part.cur_stock = before - qty
            part.save(update_fields=["cur_stock", "updated_at"])
            tx = SparePartTransaction.objects.create(
                part=part, pn=pn, desc=f"{part.desc} {part.model}".strip(), tx_type="withdraw",
                delta=-qty, before=before, after=part.cur_stock, by=by, reason=reason,
            )
            message = f"เบิกออก {qty} ({before}→{part.cur_stock})"

        elif mode == "update":
            if not part:
                return JsonResponse({"ok": False, "message": "ไม่พบ Part Number"}, status=400)
            before = part.cur_stock
            if desc:
                part.desc = desc
            part.model = _clean_str(data.get("model"), 150)
            part.cat = _clean_str(data.get("cat"), 30)
            part.sub = _clean_str(data.get("sub"), 50)
            part.mfr = _clean_str(data.get("mfr"), 100)
            part.unit = _clean_str(data.get("unit"), 10) or part.unit
            price = _to_decimal(data.get("price"), None)
            if price is not None:
                part.price = price
            min_stock = _to_int(data.get("min"), None)
            if min_stock is not None:
                part.min_stock = max(0, min_stock)
            part.location = _clean_str(data.get("loc"), 100)
            new_qty = _to_int(qty_raw, None)
            if new_qty is not None:
                part.cur_stock = max(0, new_qty)
            part.save()
            after = part.cur_stock
            tx = SparePartTransaction.objects.create(
                part=part, pn=pn, desc=desc or part.desc, tx_type="update",
                delta=after - before, before=before, after=after, by=by, reason=reason,
            )
            message = f"อัปเดต {pn} เรียบร้อย"

        elif mode == "replace":
            if not part:
                return JsonResponse({"ok": False, "message": "ไม่พบ Part Number"}, status=400)
            before = part.cur_stock
            if desc:
                part.desc = desc
            part.model = _clean_str(data.get("model"), 150)
            part.mfr = _clean_str(data.get("mfr"), 100)
            qty = _to_int(qty_raw, None)
            if qty is not None and qty_raw not in (None, ""):
                part.cur_stock = max(0, qty)
            part.save()
            tx = SparePartTransaction.objects.create(
                part=part, pn=pn, desc=desc or part.desc, tx_type="replace",
                delta=0, before=before, after=part.cur_stock, by=by, reason=reason,
            )
            message = f"บันทึกการเปลี่ยนทดแทน {pn} เรียบร้อย"

        else:
            return JsonResponse({"ok": False, "message": "โหมดไม่ถูกต้อง"}, status=400)

    log_action(
        user=request.user, action="UPDATE", module="spare_parts", object_type="SparePart",
        object_id=part.pk, description=f"{TX_LABELS.get(mode, mode)} — {pn} ({message})",
        ip_address=get_client_ip(request),
    )
    return JsonResponse({"ok": True, "message": message, "part": part.as_dict(), "tx": tx.as_dict()})


@login_required
@require_permission("internal.spare_part_edit")
@require_POST
def api_import(request):
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "message": "ข้อมูลไม่ถูกต้อง"}, status=400)

    import_mode = data.get("import_mode")
    rows = data.get("rows") or []
    if import_mode not in ("merge", "full", "reset"):
        return JsonResponse({"ok": False, "message": "โหมด import ไม่ถูกต้อง"}, status=400)
    if not isinstance(rows, list) or not rows:
        return JsonResponse({"ok": False, "message": "ไม่พบข้อมูลนำเข้า"}, status=400)

    cleaned = []
    for r in rows:
        pn = _clean_str(r.get("pn"), 30).upper()
        if not pn:
            continue
        cleaned.append({
            "pn": pn, "desc": _clean_str(r.get("desc"), 200),
            "model": _clean_str(r.get("model"), 150),
            "cat": _clean_str(r.get("cat"), 30), "sub": _clean_str(r.get("sub"), 50),
            "mfr": _clean_str(r.get("mfr"), 100), "unit": _clean_str(r.get("unit"), 10) or "EA",
            "price": _to_decimal(r.get("price")),
            "min": max(0, _to_int(r.get("min"))), "cur": max(0, _to_int(r.get("cur"))),
            "loc": _clean_str(r.get("loc"), 100), "lead": _clean_str(r.get("lead"), 20) or "7",
            "remarks": _clean_str(r.get("remarks"), 200),
        })
    if not cleaned:
        return JsonResponse({"ok": False, "message": "ไม่พบข้อมูลนำเข้าที่ถูกต้อง"}, status=400)

    added = updated = 0
    with transaction.atomic():
        if import_mode == "reset":
            SparePartTransaction.objects.all().delete()
            SparePart.objects.all().delete()
            for row in cleaned:
                part = SparePart.objects.create(
                    pn=row["pn"], desc=row["desc"], model=row["model"], cat=row["cat"], sub=row["sub"],
                    mfr=row["mfr"], unit=row["unit"], price=row["price"], min_stock=row["min"],
                    cur_stock=row["cur"], location=row["loc"], lead_time_days=row["lead"], remarks=row["remarks"],
                )
            SparePartTransaction.objects.create(
                pn="[IMPORT]", desc=f"Full Reset {len(cleaned)} รายการ", tx_type="new",
                delta=0, before=0, after=0, by="System", reason="Full Reset",
            )
            message = f"รีเซ็ตและโหลดข้อมูลใหม่ {len(cleaned)} รายการ"
        elif import_mode == "full":
            SparePart.objects.all().delete()
            for row in cleaned:
                SparePart.objects.create(
                    pn=row["pn"], desc=row["desc"], model=row["model"], cat=row["cat"], sub=row["sub"],
                    mfr=row["mfr"], unit=row["unit"], price=row["price"], min_stock=row["min"],
                    cur_stock=row["cur"], location=row["loc"], lead_time_days=row["lead"], remarks=row["remarks"],
                )
            SparePartTransaction.objects.create(
                pn="[IMPORT]", desc=f"Full Replace {len(cleaned)} รายการ", tx_type="new",
                delta=0, before=0, after=0, by="System", reason="Full Replace",
            )
            message = f"Full Replace {len(cleaned)} รายการ"
        else:
            for row in cleaned:
                existing = SparePart.objects.filter(pn=row["pn"]).first()
                if existing:
                    if existing.cur_stock != row["cur"]:
                        before = existing.cur_stock
                        existing.cur_stock = row["cur"]
                        existing.save(update_fields=["cur_stock", "updated_at"])
                        SparePartTransaction.objects.create(
                            part=existing, pn=row["pn"], desc=f"{row['desc']} {row['model']}".strip(),
                            tx_type="update", delta=row["cur"] - before, before=before, after=row["cur"],
                            by="Excel Import", reason="Sync จาก Excel",
                        )
                        updated += 1
                else:
                    part = SparePart.objects.create(
                        pn=row["pn"], desc=row["desc"], model=row["model"], cat=row["cat"], sub=row["sub"],
                        mfr=row["mfr"], unit=row["unit"], price=row["price"], min_stock=row["min"],
                        cur_stock=row["cur"], location=row["loc"], lead_time_days=row["lead"], remarks=row["remarks"],
                    )
                    SparePartTransaction.objects.create(
                        part=part, pn=row["pn"], desc=f"{row['desc']} {row['model']}".strip(), tx_type="new",
                        delta=row["cur"], before=0, after=row["cur"], by="Excel Import", reason="Import ใหม่",
                    )
                    added += 1
            message = f"Merge สำเร็จ — อัปเดต {updated} เพิ่มใหม่ {added} รายการ"

    log_action(
        user=request.user, action="UPDATE", module="spare_parts", object_type="SparePart",
        object_id="", description=f"Import ({import_mode}) — {message}",
        ip_address=get_client_ip(request),
    )

    parts = SparePart.objects.all().order_by("pn")
    txlog = SparePartTransaction.objects.all()[:2000]
    return JsonResponse({
        "ok": True, "message": message,
        "parts": [p.as_dict() for p in parts],
        "txlog": [t.as_dict() for t in txlog],
    })

from django.db import models


class SparePart(models.Model):
    """One spare-part inventory row (Support Team's spare-parts store)."""

    pn = models.CharField("Part Number", max_length=30, unique=True)
    desc = models.CharField("Description (EN)", max_length=200)
    descth = models.CharField("รายละเอียดเพิ่มเติม", max_length=200, blank=True)
    cat = models.CharField("Category", max_length=30, blank=True)
    sub = models.CharField("Sub-Category", max_length=50, blank=True)
    mfr = models.CharField("Manufacturer", max_length=100, blank=True)
    model = models.CharField("Model / Spec", max_length=150, blank=True)
    unit = models.CharField("Unit", max_length=10, default="EA")
    price = models.DecimalField("Unit Price (THB)", max_digits=12, decimal_places=2, default=0)
    min_stock = models.PositiveIntegerField("Min Stock", default=0)
    cur_stock = models.PositiveIntegerField("Current Stock", default=0)
    max_stock = models.PositiveIntegerField("Max Stock", default=0)
    location = models.CharField("Location", max_length=100, blank=True)
    lead_time_days = models.CharField("Lead Time (วัน)", max_length=20, blank=True)
    remarks = models.CharField("หมายเหตุ", max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["pn"]

    def __str__(self):
        return self.pn

    @property
    def status(self):
        if self.cur_stock <= 0:
            return "OUT OF STOCK"
        if self.min_stock > 0 and (self.cur_stock / self.min_stock) < 0.5:
            return "LOW STOCK"
        return "IN STOCK"

    @property
    def pct(self):
        if not self.min_stock:
            return 100 if self.cur_stock > 0 else 0
        return round((self.cur_stock / self.min_stock) * 100)

    def as_dict(self):
        return {
            "id": self.pk,
            "pn": self.pn,
            "desc": self.desc,
            "descth": self.descth,
            "cat": self.cat,
            "sub": self.sub,
            "mfr": self.mfr,
            "model": self.model,
            "unit": self.unit,
            "price": float(self.price),
            "min": self.min_stock,
            "cur": self.cur_stock,
            "max": self.max_stock,
            "loc": self.location,
            "lead": self.lead_time_days,
            "remarks": self.remarks,
        }


class SparePartTransaction(models.Model):
    """Transaction log row — kept even if the related SparePart is later
    deleted, since pn/desc are snapshotted at the time of the transaction
    (matches the audit-log pattern used elsewhere in this system)."""

    class TxType(models.TextChoices):
        RECEIVE = "receive", "รับเข้า"
        WITHDRAW = "withdraw", "เบิกออก"
        UPDATE = "update", "แก้ไข"
        REPLACE = "replace", "เปลี่ยนทดแทน"
        NEW = "new", "เพิ่มใหม่"

    part = models.ForeignKey(SparePart, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    pn = models.CharField(max_length=30)
    desc = models.CharField(max_length=200, blank=True)
    tx_type = models.CharField(max_length=10, choices=TxType.choices)
    delta = models.IntegerField(default=0)
    before = models.IntegerField(default=0)
    after = models.IntegerField(default=0)
    by = models.CharField("ผู้ดำเนินการ", max_length=100, blank=True)
    reason = models.CharField("หมายเหตุ / เหตุผล", max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    occurred_label = models.CharField(
        "วันที่ (สำหรับข้อมูลนำเข้า)", max_length=40, blank=True,
        help_text="ใช้เฉพาะรายการที่ import มาจากประวัติเดิม ซึ่งไม่มี timestamp จริง",
    )

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.tx_type} {self.pn} ({self.delta:+d})"

    def display_ts(self):
        if self.occurred_label:
            return self.occurred_label
        return self.created_at.strftime("%d/%m/%Y %H:%M")

    def as_dict(self):
        return {
            "id": self.pk,
            "type": self.tx_type,
            "pn": self.pn,
            "desc": self.desc,
            "delta": self.delta,
            "before": self.before,
            "after": self.after,
            "by": self.by,
            "reason": self.reason,
            "ts": self.display_ts(),
        }

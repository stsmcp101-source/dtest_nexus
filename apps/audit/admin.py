from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "username_snapshot", "action", "module", "object_type", "object_id", "ip_address")
    list_filter = ("action", "module")
    search_fields = ("username_snapshot", "description", "object_id")
    date_hierarchy = "timestamp"
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

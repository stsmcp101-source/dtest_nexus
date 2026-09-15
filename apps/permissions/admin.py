from django.contrib import admin

from .models import Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "is_system", "member_count", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Department, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "employee_id", "department", "status", "is_active", "last_login")
    list_filter = ("status", "is_active", "department", "groups")
    search_fields = ("username", "email", "employee_id", "first_name", "last_name")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Organisation", {
            "fields": ("employee_id", "department", "position", "phone_number", "status", "must_change_password"),
        }),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")

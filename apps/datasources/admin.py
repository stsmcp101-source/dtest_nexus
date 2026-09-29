from django.contrib import admin

from .models import DatabaseConnection


@admin.register(DatabaseConnection)
class DatabaseConnectionAdmin(admin.ModelAdmin):
    # encrypted_password is deliberately excluded — never surface the raw
    # ciphertext (or a plaintext field) in a generic admin form; use the
    # in-app "Database Connections" page (Settings) to set a password.
    list_display = ("name", "server", "database_name", "is_active", "last_test_ok", "last_test_at")
    list_filter = ("is_active", "last_test_ok")
    search_fields = ("name", "server", "database_name")
    exclude = ("encrypted_password",)
    readonly_fields = ("last_test_ok", "last_test_at", "last_test_message", "created_by", "created_at", "updated_at")

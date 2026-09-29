from django.contrib import admin
from django.utils.html import format_html

from .models import ModuleDefinition, Standard, SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()


@admin.register(ModuleDefinition)
class ModuleDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "short_tag", "order", "is_active", "is_available")
    list_editable = ("order", "is_active", "is_available")
    search_fields = ("name", "code")


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ("logo_preview", "name", "url", "order", "is_active")
    list_display_links = ("logo_preview", "name")
    list_editable = ("order", "is_active")
    search_fields = ("name", "description", "url")
    fields = ("name", "description", "logo", "logo_preview", "url", "order", "is_active")
    readonly_fields = ("logo_preview",)

    @admin.display(description="ตัวอย่างโลโก้")
    def logo_preview(self, obj):
        if not obj.logo:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="height:44px;max-width:160px;object-fit:contain;'
            'background:#fff;border:1px solid #ddd;border-radius:6px;padding:4px">',
            obj.logo.url,
        )

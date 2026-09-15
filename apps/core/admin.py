from django.contrib import admin

from .models import ModuleDefinition, SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()


@admin.register(ModuleDefinition)
class ModuleDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "short_tag", "order", "is_active", "is_available")
    list_editable = ("order", "is_active", "is_available")
    search_fields = ("name", "code")

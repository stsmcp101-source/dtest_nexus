from django.contrib import admin

from .models import Document, DocumentCategory, DocumentSource, DocumentType


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "order")


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code")


@admin.register(DocumentSource)
class DocumentSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "provider_type", "is_active")
    list_filter = ("provider_type", "is_active")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("document_code", "document_name", "category", "status", "source", "updated_at")
    list_filter = ("category", "status", "source")
    search_fields = ("document_code", "document_name", "business_unit")
    readonly_fields = ("file_size", "file_type", "created_at", "updated_at")

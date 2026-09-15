from django import forms
from django.conf import settings

from .models import Document, DocumentCategory, DocumentSource, DocumentType, EquipmentSpec
from .storage import validate_upload


class DocumentForm(forms.ModelForm):
    """
    Used for editing an existing document, and for the secondary
    "link an external document" flow. Category and Document type are
    intentionally not user-facing fields — category is auto-detected
    from the name (see storage.detect_category_code), and document type
    is optional metadata not needed for the common case.
    """

    class Meta:
        model = Document
        fields = [
            "document_code", "document_name",
            "source", "file", "external_url", "document_year", "description",
        ]
        widgets = {
            "document_code": forms.TextInput(attrs={"class": "form-input", "placeholder": "เช่น DEV-ENG-0142"}),
            "document_name": forms.TextInput(attrs={"class": "form-input"}),
            "source": forms.Select(attrs={"class": "form-input"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-input"}),
            "external_url": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://drive.google.com/..."}),
            "document_year": forms.NumberInput(attrs={"class": "form-input", "placeholder": "เช่น 2025", "min": 2000, "max": 2100}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # document_code is only ever typed by hand for the external-link
        # flow (no filename to derive it from there). Once a document
        # exists — whether auto-coded from a filename or typed in — it's
        # a permanent identifier and stops being user-editable.
        if self.instance and self.instance.pk:
            del self.fields["document_code"]

    def clean(self):
        cleaned = super().clean()
        source = cleaned.get("source")
        file = cleaned.get("file")
        external_url = cleaned.get("external_url")

        if source and source.provider_type == DocumentSource.ProviderType.LOCAL:
            if not file and not (self.instance and self.instance.file):
                raise forms.ValidationError("กรุณาแนบไฟล์สำหรับแหล่งที่มาแบบ Local")
            if file:
                validate_upload(
                    file,
                    getattr(settings, "DOCUMENTS_ALLOWED_EXTENSIONS", []),
                    getattr(settings, "DOCUMENTS_MAX_UPLOAD_SIZE_MB", 25),
                )
        elif source:
            if not external_url:
                raise forms.ValidationError("กรุณาระบุ URL สำหรับแหล่งที่มานี้")
        return cleaned


class EquipmentSpecForm(forms.ModelForm):
    class Meta:
        model = EquipmentSpec
        fields = ["year", "indoor_unit", "outdoor_unit", "report_dev_code", "report_sam_code"]
        widgets = {
            "year": forms.NumberInput(attrs={"class": "form-input", "placeholder": "เช่น 2025", "min": 2000, "max": 2100}),
            "indoor_unit": forms.TextInput(attrs={"class": "form-input", "placeholder": "เช่น MSZ-GS20VFD2-A1, MSZ-GS35VFD2-A2"}),
            "outdoor_unit": forms.TextInput(attrs={"class": "form-input", "placeholder": "เช่น MUZ-GS20VFD2-A1"}),
            "report_dev_code": forms.TextInput(attrs={"class": "form-input", "placeholder": "เช่น DEV-20-760-0047"}),
            "report_sam_code": forms.TextInput(attrs={"class": "form-input", "placeholder": "เช่น SAM-20-760-0052"}),
        }


class EquipmentSpecImportForm(forms.Form):
    excel_file = forms.FileField(widget=forms.ClearableFileInput(attrs={"class": "form-input", "accept": ".xlsx"}))


class DocumentCategoryForm(forms.ModelForm):
    class Meta:
        model = DocumentCategory
        fields = ["code", "name", "order"]


class DocumentTypeForm(forms.ModelForm):
    class Meta:
        model = DocumentType
        fields = ["code", "name"]

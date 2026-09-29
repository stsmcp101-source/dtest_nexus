from django import forms
from django.core.validators import FileExtensionValidator

from apps.core.models import SystemSettings

from .tool_icons import TOOL_ICONS

ICON_MAX_MB = 2
# No SVG: an uploaded SVG opened straight from /media/ could run script on this origin.
ICON_EXTENSIONS = ["png", "jpg", "jpeg", "webp", "gif"]


class ToolLinkSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = ["tool_link_approve_doc", "tool_link_kace", "tool_link_pscapa"]
        widgets = {
            "tool_link_approve_doc": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://..."}),
            "tool_link_kace": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://..."}),
            "tool_link_pscapa": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://..."}),
        }
        labels = {
            "tool_link_approve_doc": "Approve Doc — ลิงก์ Power Apps",
            "tool_link_kace": "KACE Systems — ลิงก์ระบบ",
            "tool_link_pscapa": "PScapa — ลิงก์ระบบ",
        }


class ToolIconSettingsForm(forms.Form):
    """One optional logo upload + one "back to default icon" checkbox per Tools tile."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, _section, _name, _svg in TOOL_ICONS:
            self.fields[f"icon_{key}"] = forms.ImageField(
                required=False,
                validators=[FileExtensionValidator(ICON_EXTENSIONS)],
                widget=forms.FileInput(attrs={"class": "ti-input", "accept": ",".join("." + e for e in ICON_EXTENSIONS)}),
            )
            self.fields[f"reset_{key}"] = forms.BooleanField(required=False)

    def clean(self):
        cleaned = super().clean()
        for key, _section, _name, _svg in TOOL_ICONS:
            upload = cleaned.get(f"icon_{key}")
            if upload and upload.size > ICON_MAX_MB * 1024 * 1024:
                self.add_error(f"icon_{key}", f"ขนาดไฟล์เกิน {ICON_MAX_MB} MB")
        return cleaned

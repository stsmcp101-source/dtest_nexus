from django import forms
from django.core.validators import FileExtensionValidator
from apps.utilities.forms import ICON_MAX_MB, ICON_EXTENSIONS
from .icons import INTERNAL_ICONS


class InternalIconSettingsForm(forms.Form):
    """One optional logo upload + one "back to default icon" checkbox per Tools tile."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, _section, _name, _svg in INTERNAL_ICONS:
            self.fields[f"icon_{key}"] = forms.ImageField(
                required=False,
                validators=[FileExtensionValidator(ICON_EXTENSIONS)],
                widget=forms.FileInput(attrs={"class": "ti-input", "accept": ",".join("." + e for e in ICON_EXTENSIONS)}),
            )
            self.fields[f"reset_{key}"] = forms.BooleanField(required=False)

    def clean(self):
        cleaned = super().clean()
        for key, _section, _name, _svg in INTERNAL_ICONS:
            upload = cleaned.get(f"icon_{key}")
            if upload and upload.size > ICON_MAX_MB * 1024 * 1024:
                self.add_error(f"icon_{key}", f"ขนาดไฟล์เกิน {ICON_MAX_MB} MB")
        return cleaned

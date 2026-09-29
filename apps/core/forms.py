from django import forms
from django.db.models import Max

from .models import AboutTopic, ModuleDefinition, Standard, SystemSettings


class HeroBackgroundForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = ["hero_bg_image", "hero_bg_video"]
        labels = {
            "hero_bg_image": "รูปภาพพื้นหลัง",
            "hero_bg_video": "วิดีโอพื้นหลัง (แสดงทับรูปภาพ ถ้ามี)",
        }


ModuleImageFormSet = forms.modelformset_factory(
    ModuleDefinition,
    fields=["background_image", "background_image_speed"],
    extra=0,
    labels={"background_image_speed": "ความเร็วภาพเคลื่อนไหว (ตัวคูณ)"},
    widgets={
        "background_image_speed": forms.NumberInput(attrs={
            "class": "form-input", "step": "0.1", "min": "0.1", "max": "10", "style": "max-width:120px;",
        }),
    },
)


AboutTopicFormSet = forms.modelformset_factory(
    AboutTopic,
    fields=["title_en", "title_th", "body", "image"],
    extra=0,
    labels={
        "title_en": "หัวข้อ (English)",
        "title_th": "ชื่อภาษาไทย",
        "body": "ข้อความ",
        "image": "รูปภาพ (ไม่บังคับ)",
    },
    widgets={
        "title_en": forms.TextInput(attrs={"class": "form-input"}),
        "title_th": forms.TextInput(attrs={"class": "form-input"}),
        "body": forms.Textarea(attrs={"class": "form-input", "rows": 4}),
    },
)


class StandardForm(forms.ModelForm):
    class Meta:
        model = Standard
        fields = ["name", "description", "logo", "url", "order", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "เช่น AHRI"}),
            "description": forms.TextInput(attrs={"class": "form-input"}),
            "logo": forms.FileInput(attrs={"class": "std-logo-input", "accept": "image/*"}),
            "url": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://..."}),
            "order": forms.NumberInput(attrs={"class": "form-input", "min": 0, "placeholder": "ต่อท้าย"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Left blank, a new row goes after the existing ones instead of jumping to the top at 0.
        self.fields["order"].required = False
        if not self.instance.pk:
            self.initial["order"] = None

    def clean_order(self):
        order = self.cleaned_data["order"]
        if order is None:
            order = (Standard.objects.aggregate(m=Max("order"))["m"] or 0) + 1
        return order


StandardFormSet = forms.modelformset_factory(Standard, form=StandardForm, extra=0, can_delete=True)

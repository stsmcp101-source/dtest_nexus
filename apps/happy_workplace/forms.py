from django import forms

import re

from .models import (
    Announcement,
    HappyWorkplaceSettings,
    PosterImage,
    SquaresSettings,
    SquaresWord,
    TypingSettings,
    WordleSettings,
)


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "body", "category", "is_pinned"]
        labels = {
            "title": "หัวข้อ",
            "body": "รายละเอียด",
            "category": "หมวดหมู่",
            "is_pinned": "ปักหมุดไว้บนสุด",
        }
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input"}),
            "body": forms.Textarea(attrs={"class": "form-input", "rows": 5}),
            "category": forms.Select(attrs={"class": "form-input"}),
        }


class PosterImageForm(forms.ModelForm):
    class Meta:
        model = PosterImage
        fields = ["image", "caption", "order"]
        labels = {
            "image": "ไฟล์ภาพ (jpg, png, webp, gif ฯลฯ)",
            "caption": "คำบรรยายภาพ (ไม่บังคับ)",
            "order": "ลำดับการแสดงผล",
        }
        widgets = {
            "image": forms.ClearableFileInput(attrs={"class": "form-input"}),
            "caption": forms.TextInput(attrs={"class": "form-input"}),
            "order": forms.NumberInput(attrs={"class": "form-input"}),
        }


class WordleSettingsForm(forms.ModelForm):
    class Meta:
        model = WordleSettings
        fields = ["session_minutes", "max_guesses", "penalty_per_wrong"]
        labels = {
            "session_minutes": "เวลาต่อรอบ (นาที)",
            "max_guesses": "จำนวนครั้งที่ทายได้ต่อคำ",
            "penalty_per_wrong": "คะแนนที่ติดลบต่อการทายผิด 1 ครั้ง",
        }
        widgets = {
            "session_minutes": forms.NumberInput(attrs={"class": "form-input", "min": 1, "max": 60}),
            "max_guesses": forms.NumberInput(attrs={"class": "form-input", "min": 1, "max": 20}),
            "penalty_per_wrong": forms.NumberInput(attrs={"class": "form-input", "min": 0, "max": 10}),
        }


_PLAY_LIMIT_WIDGET = forms.NumberInput(attrs={"class": "form-input", "min": 0, "max": 100})


class PlayLimitForm(forms.ModelForm):
    """All daily-limited features at once (manage page)."""

    class Meta:
        model = HappyWorkplaceSettings
        fields = [
            "wordle_play_limit", "squares_play_limit", "typing_play_limit",
            "fortune_play_limit", "phone_analysis_play_limit", "dream_play_limit",
        ]
        labels = {
            "wordle_play_limit": "Wordle — เล่นได้ต่อวัน (ครั้ง)",
            "squares_play_limit": "Squares — เล่นได้ต่อวัน (ครั้ง)",
            "typing_play_limit": "พิมพ์เร็ว — เล่นได้ต่อวัน (ครั้ง)",
            "fortune_play_limit": "เซียมซี — เล่นได้ต่อวัน (ครั้ง)",
            "phone_analysis_play_limit": "วิเคราะห์เบอร์ — เล่นได้ต่อวัน (ครั้ง)",
            "dream_play_limit": "ทำนายฝัน — เล่นได้ต่อวัน (ครั้ง)",
        }
        widgets = {f: _PLAY_LIMIT_WIDGET for f in fields}


def game_play_limit_form(game):
    """Form class holding just one game's daily limit (game settings box)."""
    field = f"{game}_play_limit"

    class GamePlayLimitForm(forms.ModelForm):
        class Meta:
            model = HappyWorkplaceSettings
            fields = [field]
            labels = {field: "จำนวนครั้งที่เล่นได้ต่อวัน (0 = ไม่จำกัด)"}
            widgets = {field: _PLAY_LIMIT_WIDGET}

    return GamePlayLimitForm


class SquaresSettingsForm(forms.ModelForm):
    class Meta:
        model = SquaresSettings
        fields = ["session_minutes"]
        labels = {"session_minutes": "เวลาต่อรอบ (นาที)"}
        widgets = {"session_minutes": forms.NumberInput(attrs={"class": "form-input", "min": 1, "max": 60})}


class TypingSettingsForm(forms.ModelForm):
    class Meta:
        model = TypingSettings
        fields = ["session_minutes"]
        labels = {"session_minutes": "เวลาต่อรอบ (นาที)"}
        widgets = {"session_minutes": forms.NumberInput(attrs={"class": "form-input", "min": 1, "max": 60})}


class SquaresWordForm(forms.ModelForm):
    class Meta:
        model = SquaresWord
        fields = ["word", "meaning", "category"]
        labels = {
            "word": "คำศัพท์ (ภาษาอังกฤษ A-Z, 3-12 ตัวอักษร ไม่มีเว้นวรรค)",
            "meaning": "ความหมาย (ภาษาไทย)",
            "category": "หมวดหมู่",
        }
        widgets = {
            "word": forms.TextInput(attrs={"class": "form-input", "maxlength": 12, "style": "text-transform:uppercase;"}),
            "meaning": forms.TextInput(attrs={"class": "form-input", "maxlength": 200}),
            "category": forms.Select(attrs={"class": "form-input"}),
        }

    def clean_word(self):
        word = self.cleaned_data["word"].strip().upper()
        if not re.fullmatch(r"[A-Z]{3,12}", word):
            raise forms.ValidationError("ใช้ได้เฉพาะตัวอักษรภาษาอังกฤษ A-Z ความยาว 3-12 ตัวอักษร ไม่มีเว้นวรรคหรือเครื่องหมาย")
        clash = SquaresWord.objects.filter(word=word)
        if self.instance.pk:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError("มีคำนี้อยู่ในคลังแล้ว")
        return word


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    """ImageField that accepts several files at once (each one is still
    validated as a real image)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"class": "form-input", "accept": "image/*"}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        clean_one = super().clean
        if isinstance(data, (list, tuple)):
            return [clean_one(d, initial) for d in data]
        return [clean_one(data, initial)]


class FortuneSlipUploadForm(forms.Form):
    images = MultipleImageField(label="ไฟล์ภาพคำทำนาย (เลือกได้หลายไฟล์พร้อมกัน)")
    number = forms.IntegerField(
        required=False, min_value=1, max_value=28, label="เลขที่ใบ (เฉพาะกรณีอัปโหลดไฟล์เดียวที่ชื่อไฟล์ไม่มีตัวเลข)",
        widget=forms.NumberInput(attrs={"class": "form-input", "min": 1, "max": 28}),
    )

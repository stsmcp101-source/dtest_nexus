from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group

from apps.permissions.registry import get_registered_permissions_queryset

from .models import Department, User


class StyledAuthenticationForm(AuthenticationForm):
    """Wraps Django's AuthenticationForm to apply the design-system input
    classes; validation logic is untouched (still uses Django's
    ModelBackend + password hashers under the hood)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "class": "form-input", "placeholder": "ชื่อผู้ใช้งาน", "autofocus": True,
        })
        self.fields["password"].widget.attrs.update({
            "class": "form-input", "placeholder": "รหัสผ่าน",
        })


class PermissionMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Shows the permission's plain-English name (e.g. 'Can upload
    document') instead of Django's default 'app | model | name' str(),
    which is unreadable in the checkbox list."""

    def label_from_instance(self, obj):
        return obj.name


class UserForm(forms.ModelForm):
    """Admin-facing create/edit form for the User model."""

    roles = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(), required=False, widget=forms.CheckboxSelectMultiple,
        label="บทบาท (Role)",
    )
    extra_permissions = PermissionMultipleChoiceField(
        queryset=get_registered_permissions_queryset(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="สิทธิ์เพิ่มเติมเฉพาะบุคคล",
        help_text=(
            "มอบสิทธิ์เฉพาะบุคคลนอกเหนือจาก Role ที่ได้รับ เช่น อนุญาตให้ผู้ใช้ที่มี Role "
            "'User' สามารถอัปโหลดเอกสารใน Document Data ได้เป็นรายบุคคล โดยไม่ต้องเปลี่ยน Role"
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput, required=False,
        help_text="เว้นว่างไว้หากไม่ต้องการเปลี่ยนรหัสผ่าน",
    )

    class Meta:
        model = User
        fields = [
            "username", "email", "employee_id", "first_name", "last_name",
            "department", "position", "phone_number", "status", "is_active",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-input"}),
            "email": forms.EmailInput(attrs={"class": "form-input"}),
            "employee_id": forms.TextInput(attrs={"class": "form-input"}),
            "first_name": forms.TextInput(attrs={"class": "form-input"}),
            "last_name": forms.TextInput(attrs={"class": "form-input"}),
            "department": forms.Select(attrs={"class": "form-input"}),
            "position": forms.TextInput(attrs={"class": "form-input"}),
            "phone_number": forms.TextInput(attrs={"class": "form-input"}),
            "status": forms.Select(attrs={"class": "form-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["roles"].initial = self.instance.groups.all()
            self.fields["extra_permissions"].initial = self.instance.user_permissions.all()

    def save(self, commit=True):
        user = super().save(commit=False)
        raw_password = self.cleaned_data.get("password")
        if raw_password:
            user.set_password(raw_password)
        if commit:
            user.save()
            user.groups.set(self.cleaned_data["roles"])
            # Individual, per-user permission grants on top of the Role
            # (e.g. give one specific User the document.upload
            # permission without changing their Role). Django's
            # has_perm() already combines group permissions with
            # user_permissions automatically, so no extra check-time
            # logic is needed anywhere else in the codebase.
            user.user_permissions.set(self.cleaned_data["extra_permissions"])
        return user


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "code"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "code": forms.TextInput(attrs={"class": "form-input"}),
        }

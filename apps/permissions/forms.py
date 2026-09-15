from django import forms
from django.contrib.auth.models import Group, Permission

from .models import Role


class RoleForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.select_related("content_type").all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Role
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["permissions"].initial = self.instance.group.permissions.all()

    def save(self, commit=True):
        role = super().save(commit=False)
        if not role.pk or not getattr(role, "group_id", None):
            group = Group.objects.create(name=self.cleaned_data["name"])
            role.group = group
        else:
            role.group.name = self.cleaned_data["name"]
            role.group.save(update_fields=["name"])
        if commit:
            role.save()
            role.group.permissions.set(self.cleaned_data["permissions"])
        return role

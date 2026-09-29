from django import forms

from .models import DatabaseConnection


class DatabaseConnectionForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "", "autocomplete": "new-password"}),
        label="Password",
        help_text="เว้นว่างไว้เพื่อคงรหัสผ่านเดิม",
    )

    class Meta:
        model = DatabaseConnection
        fields = ["name", "server", "port", "database_name", "username", "driver", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Company SQL Server"}),
            "server": forms.TextInput(attrs={"class": "form-input", "placeholder": "192.168.1.100"}),
            "port": forms.NumberInput(attrs={"class": "form-input", "placeholder": "1433"}),
            "database_name": forms.TextInput(attrs={"class": "form-input", "placeholder": "CompanyDB"}),
            "username": forms.TextInput(attrs={"class": "form-input", "placeholder": "readonly_user"}),
            "driver": forms.TextInput(attrs={"class": "form-input", "placeholder": "ODBC Driver 18 for SQL Server"}),
        }
        labels = {
            "name": "Name",
            "server": "Server",
            "database_name": "Database",
            "username": "Username",
            "driver": "Driver",
            "is_active": "Active (แสดงใน Data Explorer)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["password"].widget.attrs["placeholder"] = "•" * 10

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw_password = self.cleaned_data.get("password")
        if raw_password:
            instance.set_password(raw_password)
        if commit:
            instance.save()
        return instance


class PrimaryDatabaseSettingsForm(forms.Form):
    """Not a ModelForm — this edits DATABASE_* keys in .env (see
    env_utils.py), not a database row. Takes effect only after the
    server is restarted; never migrates existing data."""

    ENGINE_CHOICES = [
        ("sqlite", "SQLite (ไฟล์ในเครื่อง)"),
        ("mssql", "Microsoft SQL Server"),
    ]

    engine = forms.ChoiceField(
        choices=ENGINE_CHOICES, label="ประเภทฐานข้อมูล",
        widget=forms.Select(attrs={"class": "form-input"}),
    )
    name = forms.CharField(
        label="Database Name / ไฟล์",
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    host = forms.CharField(
        required=False, label="Host / Server",
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "192.168.1.100"}),
    )
    port = forms.CharField(
        required=False, label="Port",
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "1433"}),
    )
    user = forms.CharField(
        required=False, label="Username",
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    password = forms.CharField(
        required=False, label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-input", "autocomplete": "new-password"}),
        help_text="เว้นว่างไว้เพื่อคงรหัสผ่านเดิม",
    )
    odbc_driver = forms.CharField(
        required=False, label="ODBC Driver",
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "ODBC Driver 18 for SQL Server"}),
    )
    confirm = forms.BooleanField(
        label="ฉันเข้าใจว่าการเปลี่ยนแปลงนี้จะมีผลหลังรีสตาร์ทระบบเท่านั้น และไม่ได้ย้ายข้อมูลเดิมให้อัตโนมัติ",
        widget=forms.CheckboxInput(),
    )

    def clean(self):
        cleaned = super().clean()
        engine = cleaned.get("engine")
        if engine == "mssql":
            for field in ("name", "host", "user"):
                if not cleaned.get(field):
                    self.add_error(field, "จำเป็นสำหรับ SQL Server")
            port = (cleaned.get("port") or "").strip()
            if port and not port.isdigit():
                self.add_error("port", "ต้องเป็นตัวเลข")
        elif engine == "sqlite" and not cleaned.get("name"):
            self.add_error("name", "จำเป็นต้องระบุ path ไฟล์ฐานข้อมูล")
        return cleaned

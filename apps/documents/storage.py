"""
Storage-provider abstraction (rule #21 / #22).

`Document.source.provider_type` decides where a document's bytes live.
Views and templates should ask *this module* for an openable/downloadable
URL rather than reaching into `document.file.url` directly, so that
adding a real Google Drive / SharePoint integration later means adding
a branch here — not changing every view and template that opens or
downloads a document.

Only the LOCAL provider is implemented in this phase, exactly as rule
#22 allows ("ไม่จำเป็นต้อง Implement ทุก Provider ใน Phase แรก").
"""
import re

from django.core.exceptions import ValidationError

from .models import DocumentSource


class UnsupportedProviderError(Exception):
    pass


_YEAR_PATTERN = re.compile(r"(?:SAM|DEV)-(\d{2})-")


def detect_document_year(name: str) -> int | None:
    """
    Documents are coded like SAM-25-760... / DEV-25-...  where the two
    digits right after SAM/DEV are the year (25 -> 2025). Returns None
    when the name doesn't follow that convention, so the caller can fall
    back to whatever the uploader typed in the Year field.
    """
    match = _YEAR_PATTERN.search(name.upper())
    if not match:
        return None
    return 2000 + int(match.group(1))


def get_open_url(document):
    """Return a URL the browser can open to view/preview this document."""
    provider = document.source.provider_type
    if provider == DocumentSource.ProviderType.LOCAL:
        if not document.file:
            raise UnsupportedProviderError("This document has no local file attached.")
        return document.file.url
    if provider in (
        DocumentSource.ProviderType.GOOGLE_DRIVE,
        DocumentSource.ProviderType.SHAREPOINT,
        DocumentSource.ProviderType.NETWORK_DRIVE,
        DocumentSource.ProviderType.EXTERNAL_URL,
    ):
        if not document.external_url:
            raise UnsupportedProviderError(
                f"This document's source is {document.source.get_provider_type_display()}, "
                "but no external URL has been set."
            )
        return document.external_url
    raise UnsupportedProviderError(f"Unknown storage provider: {provider}")


def get_download_url(document):
    """
    For LOCAL files this is the same as the open URL. For an external
    provider, a genuine "force download" typically requires that
    provider's API (out of scope for phase 1); we surface the same
    reference URL so the action is never silently broken.
    """
    return get_open_url(document)


def detect_category_code(name: str) -> str:
    """
    The business only ever produces two lines of documents, encoded
    directly in the file/document name — SAM = Mass, DEV = Dev — so the
    category is inferred from the name instead of asking the uploader to
    pick it from a dropdown. Anything without "SAM" in it defaults to
    Dev, since that covers both an explicit "DEV" and any other naming.
    """
    return "mass" if "SAM" in name.upper() else "dev"


def validate_upload(uploaded_file, allowed_extensions, max_size_mb):
    ext = uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else ""
    if allowed_extensions and ext not in allowed_extensions:
        raise ValidationError(f"ไม่รองรับไฟล์นามสกุล .{ext}")
    max_bytes = max_size_mb * 1024 * 1024
    if uploaded_file.size > max_bytes:
        raise ValidationError(f"ขนาดไฟล์เกิน {max_size_mb} MB")

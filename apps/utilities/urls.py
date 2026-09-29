from django.urls import path

from . import views

app_name = "utilities"

urlpatterns = [
    path("", views.index, name="index"),
    path("link-settings/", views.link_settings, name="link_settings"),
    path("icon-settings/", views.icon_settings, name="icon_settings"),

    path("pdf-edit/", views.pdf_edit, name="pdf_edit"),
    path("pdf-edit/page-count/", views.pdf_page_count, name="pdf_page_count"),
    path("pdf-edit/merge/", views.pdf_merge, name="pdf_merge"),
    path("pdf-edit/split/", views.pdf_split, name="pdf_split"),
    path("pdf-edit/delete-pages/", views.pdf_delete_pages, name="pdf_delete_pages"),
    path("pdf-edit/insert/", views.pdf_insert, name="pdf_insert"),
    path("pdf-edit/encrypt/", views.pdf_encrypt, name="pdf_encrypt"),
    path("pdf-edit/decrypt/", views.pdf_decrypt, name="pdf_decrypt"),

    path("qr-code/", views.qr_code_page, name="qr_code"),
    path("qr-code/generate/", views.qr_generate, name="qr_generate"),

    path("document-converter/", views.document_converter, name="document_converter"),
    path("document-converter/images-to-pdf/", views.convert_images_to_pdf, name="convert_images_to_pdf"),
    path("document-converter/pdf-to-images/", views.convert_pdf_to_images, name="convert_pdf_to_images"),
    path("document-converter/office-to-pdf/", views.convert_office_to_pdf, name="convert_office_to_pdf"),

    path("calculators/", views.calc_group_redirect, {"group": "calculators"}, name="calculators"),
    path("calculators/<slug:tool>/", views.calc_tool, {"group": "calculators"}, name="calculators_tool"),
    path("engineering/", views.calc_group_redirect, {"group": "engineering"}, name="engineering"),
    path("engineering/saturation-temp/data/", views.ph_diagram_data, name="ph_diagram_data"),
    path("engineering/<slug:tool>/", views.calc_tool, {"group": "engineering"}, name="engineering_tool"),
]

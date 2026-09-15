from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("", views.document_list, name="list"),
    path("specs/", views.equipment_spec_list, name="spec_list"),
    path("specs/new/", views.equipment_spec_create, name="spec_create"),
    path("specs/import/", views.equipment_spec_import, name="spec_import"),
    path("specs/export/", views.equipment_spec_export, name="spec_export"),
    path("specs/<int:pk>/edit/", views.equipment_spec_edit, name="spec_edit"),
    path("specs/<int:pk>/delete/", views.equipment_spec_delete, name="spec_delete"),
    path("search-suggest/", views.document_search_suggest, name="search_suggest"),
    path("new/", views.document_create, name="create"),
    path("<int:pk>/", views.document_detail, name="detail"),
    path("<int:pk>/edit/", views.document_edit, name="edit"),
    path("<int:pk>/delete/", views.document_delete, name="delete"),
    path("<int:pk>/open/", views.document_open, name="open"),
    path("<int:pk>/download/", views.document_download, name="download"),
]

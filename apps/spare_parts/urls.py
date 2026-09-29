from django.urls import path

from . import views

app_name = "spare_parts"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/transaction/", views.api_transaction, name="api_transaction"),
    path("api/import/", views.api_import, name="api_import"),
]

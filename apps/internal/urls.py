from django.urls import path

from . import views

app_name = "internal"

urlpatterns = [
    path("icon-settings/", views.icon_settings, name="icon_settings"),
    path("", views.index, name="index"),
]

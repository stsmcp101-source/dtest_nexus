from django.urls import path

from . import views

app_name = "happy_workplace"

urlpatterns = [
    path("", views.index, name="index"),
]

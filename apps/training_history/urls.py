from django.urls import path

from . import views

app_name = "training_history"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/employee/create/", views.api_employee_create, name="api_employee_create"),
    path("api/employee/<int:pk>/update/", views.api_employee_update, name="api_employee_update"),
    path("api/employee/<int:pk>/delete/", views.api_employee_delete, name="api_employee_delete"),
    path("api/training/create/", views.api_training_create, name="api_training_create"),
    path("api/training/<int:pk>/update/", views.api_training_update, name="api_training_update"),
    path("api/training/<int:pk>/delete/", views.api_training_delete, name="api_training_delete"),
]

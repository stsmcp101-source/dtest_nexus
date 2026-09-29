from django.urls import path

from . import views

app_name = "permissions"

urlpatterns = [
    path("roles/", views.role_list, name="role_list"),
    path("roles/new/", views.role_create, name="role_create"),
    path("roles/<int:pk>/edit/", views.role_edit, name="role_edit"),
    path("roles/<int:pk>/delete/", views.role_delete, name="role_delete"),
    path("permission-matrix/", views.permission_matrix, name="permission_matrix"),
]

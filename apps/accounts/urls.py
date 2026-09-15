from django.urls import path

from .forms import StyledAuthenticationForm
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.StyledLoginView.as_view(authentication_form=StyledAuthenticationForm), name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("users/", views.user_list, name="user_list"),
    path("users/new/", views.user_create, name="user_create"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/delete/", views.user_delete, name="user_delete"),
    path("users/<int:pk>/toggle-status/", views.user_toggle_status, name="user_toggle_status"),
    path("users/<int:pk>/reset-password/", views.user_reset_password, name="user_reset_password"),
]

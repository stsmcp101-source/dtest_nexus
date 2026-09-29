from django.urls import path

from . import views

app_name = "datasources"

urlpatterns = [
    path("connections/", views.connection_list, name="connection_list"),
    path("connections/new/", views.connection_create, name="connection_create"),
    path("connections/<int:pk>/edit/", views.connection_edit, name="connection_edit"),
    path("connections/<int:pk>/delete/", views.connection_delete, name="connection_delete"),
    path("connections/test/", views.connection_test, name="connection_test"),

    path("browse/", views.browse_index, name="browse_index"),
    path("browse/tables/", views.browse_tables, name="browse_tables"),
    path("browse/data/", views.browse_data, name="browse_data"),

    path("primary-db/update/", views.primary_database_settings_update, name="primary_database_settings_update"),
    path("primary-db/test/", views.primary_database_test, name="primary_database_test"),
]

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("usage-stats/", views.usage_stats, name="usage_stats"),
    path("usage-stats/reset/", views.usage_stats_reset, name="usage_stats_reset"),
    path("settings/home-appearance/", views.home_appearance_settings, name="home_appearance_settings"),
    path("settings/about-topics/", views.about_topics_settings, name="about_topics_settings"),
    path("settings/standards/", views.standards_settings, name="standards_settings"),
]

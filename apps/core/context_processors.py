from django.conf import settings


def app_meta(request):
    return {
        "APP_NAME": getattr(settings, "APP_NAME", "dtest_nexus"),
        "APP_DISPLAY_NAME": getattr(settings, "APP_DISPLAY_NAME", "dTest.nexus"),
        "APP_VERSION": getattr(settings, "APP_VERSION", "1.0.0"),
    }

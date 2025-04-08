from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("__reload__/", include("django_browser_reload.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include('apps.accounts.urls')),
    path("tournaments/", include('apps.tournaments.urls')),
    path("matches/", include('apps.matches.urls')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
]
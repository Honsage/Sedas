from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.views import LoginView


urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Auth
    path("api/v1/auth/token/", LoginView.as_view(), name="token_obtain"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Apps
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.documents.urls")),
    path("api/v1/", include("apps.workflows.urls")),
    path("api/v1/", include("apps.signatures.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



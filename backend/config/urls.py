from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.views import LoginView

schema_view = get_schema_view(
    openapi.Info(
        title="Sedas API",
        default_version="v1",
        description=(
            "REST API системы электронного документооборота с криптографической ЭЦП (RSA-SHA256).\n\n"
            "Для авторизации получите токен через `POST /api/v1/auth/token/` "
            "и передавайте его в заголовке: `Authorization: Bearer <access_token>`"
        ),
        license=openapi.License(name="MIT"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Swagger / ReDoc
    path("api/v1/swagger.json", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("api/v1/swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("api/v1/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
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

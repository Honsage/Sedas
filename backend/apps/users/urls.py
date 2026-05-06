from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import RoleViewSet, UserAssignRoleView, UserRemoveRoleView, UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("roles", RoleViewSet, basename="role")

urlpatterns = router.urls + [
    path("users/<int:pk>/assign-role/", UserAssignRoleView.as_view(), name="user-assign-role"),
    path("users/<int:pk>/remove-role/", UserRemoveRoleView.as_view(), name="user-remove-role"),
]

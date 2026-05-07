from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("done_at", "user", "action_type", "target_type", "target_id")
    list_filter = ("action_type", "target_type")
    search_fields = ("user__email", "target_id")
    readonly_fields = ("user", "action_type", "target_type", "target_id", "done_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

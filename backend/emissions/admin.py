from django.contrib import admin
from .models import EmissionEntry, AuditTrail


@admin.register(EmissionEntry)
class EmissionEntryAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'tenant', 'source_type', 'scope', 'category',
        'activity_date', 'quantity', 'unit', 'quantity_normalized',
        'status',
    )
    list_filter = ('status', 'source_type', 'scope', 'tenant')
    search_fields = ('category', 'facility_code', 'location')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'activity_date'


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ('id', 'emission_entry', 'action', 'actor', 'timestamp')
    list_filter = ('action',)
    readonly_fields = ('timestamp',)

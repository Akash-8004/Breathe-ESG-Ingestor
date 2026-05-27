from django.contrib import admin
from .models import DataSource, IngestionRun, RawRecord


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_type', 'tenant', 'created_at')
    list_filter = ('source_type', 'tenant')
    search_fields = ('name',)


@admin.register(IngestionRun)
class IngestionRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'data_source', 'status', 'triggered_by', 'triggered_at', 'row_count', 'error_count')
    list_filter = ('status', 'data_source__source_type')
    readonly_fields = ('triggered_at', 'completed_at')


@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'ingestion_run', 'row_index', 'parse_status')
    list_filter = ('parse_status',)
    readonly_fields = ('raw_payload', 'created_at')

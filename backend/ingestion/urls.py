from django.urls import path
from .views import IngestionRunViewSet, RawRecordListView, DataSourceListView

urlpatterns = [
    path(
        'ingestion-runs/',
        IngestionRunViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='ingestion-run-list',
    ),
    path(
        'ingestion-runs/<int:pk>/',
        IngestionRunViewSet.as_view({'get': 'retrieve'}),
        name='ingestion-run-detail',
    ),
    path(
        'ingestion-runs/<int:run_id>/raw-records/',
        RawRecordListView.as_view(),
        name='raw-record-list',
    ),
    path(
        'data-sources/',
        DataSourceListView.as_view(),
        name='data-source-list',
    ),
]

from django.urls import path
from .views import (
    EmissionEntryListView,
    EmissionEntryDetailView,
    EmissionEntryApproveView,
    EmissionEntryFlagView,
    EmissionEntryRejectView,
    DashboardSummaryView,
)

urlpatterns = [
    path(
        'emission-entries/',
        EmissionEntryListView.as_view(),
        name='emission-entry-list',
    ),
    path(
        'emission-entries/<int:pk>/',
        EmissionEntryDetailView.as_view(),
        name='emission-entry-detail',
    ),
    path(
        'emission-entries/<int:pk>/approve/',
        EmissionEntryApproveView.as_view(),
        name='emission-entry-approve',
    ),
    path(
        'emission-entries/<int:pk>/flag/',
        EmissionEntryFlagView.as_view(),
        name='emission-entry-flag',
    ),
    path(
        'emission-entries/<int:pk>/reject/',
        EmissionEntryRejectView.as_view(),
        name='emission-entry-reject',
    ),
    path(
        'dashboard/summary/',
        DashboardSummaryView.as_view(),
        name='dashboard-summary',
    ),
]

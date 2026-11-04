from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    path('api/chart/', views.ChartDataAPI.as_view(), name='chart_api'),
    path('export/csv/', views.ExportCSVView.as_view(), name='export_csv'),
]

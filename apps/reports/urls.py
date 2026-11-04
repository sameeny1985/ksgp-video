from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('new/', views.ReportCreateView.as_view(), name='create'),
    path('mine/', views.MyReportsView.as_view(), name='mine'),
]

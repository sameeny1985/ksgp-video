from django.urls import path
from . import dashboard_views as views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardHomeView.as_view(), name='index'),
    path('channels/', views.MyChannelsView.as_view(), name='channels'),
    path('videos/', views.MyVideosView.as_view(), name='videos'),
    path('campaigns/', views.MyCampaignsView.as_view(), name='campaigns'),
    path('wallet/', views.WalletDashboardView.as_view(), name='wallet'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
]

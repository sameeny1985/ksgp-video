from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    path('', views.CampaignListView.as_view(), name='list'),
    path('pricing/', views.PricingView.as_view(), name='pricing'),
    path('create/', views.CampaignCreateView.as_view(), name='create'),
    path('<uuid:uuid>/', views.CampaignDetailView.as_view(), name='detail'),
    path('<uuid:uuid>/edit/', views.CampaignUpdateView.as_view(), name='edit'),
    path('<uuid:uuid>/pause/', views.pause_campaign, name='pause'),
    path('<uuid:uuid>/resume/', views.resume_campaign, name='resume'),
]

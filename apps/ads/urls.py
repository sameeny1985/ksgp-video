from django.urls import path
from . import views

app_name = 'ads'

urlpatterns = [
    path('impression/', views.track_impression, name='impression'),
    path('click/<uuid:campaign_uuid>/', views.track_click, name='click'),
    path('serve/', views.get_ads, name='serve'),
]

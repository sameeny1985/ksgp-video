from django.urls import path
from . import views
app_name = 'channels'
urlpatterns = [
    path('', views.ChannelListView.as_view(), name='list'),
    path('add/', views.ChannelCreateView.as_view(), name='add'),
    path('<slug:slug>/', views.ChannelDetailView.as_view(), name='detail'),
    path('<slug:slug>/edit/', views.ChannelUpdateView.as_view(), name='edit'),
]

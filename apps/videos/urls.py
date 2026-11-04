from django.urls import path
from . import views
app_name = 'videos'
urlpatterns = [
    path('', views.VideoListView.as_view(), name='list'),
    path('search/', views.VideoSearchView.as_view(), name='search'),
    path('category/<slug:slug>/', views.CategoryVideosView.as_view(), name='category'),
    path('add/', views.VideoCreateView.as_view(), name='add'),
    path('<slug:slug>/', views.VideoDetailView.as_view(), name='detail'),
    path('<slug:slug>/edit/', views.VideoUpdateView.as_view(), name='edit'),
    path('<slug:slug>/save/', views.toggle_save, name='save'),
    path('<slug:slug>/report/', views.report_video, name='report'),
]

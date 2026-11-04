from django.urls import path
from . import views
app_name = 'credits'
urlpatterns = [
    path('wallet/', views.WalletView.as_view(), name='wallet'),
    path('packages/', views.PackageListView.as_view(), name='packages'),
]

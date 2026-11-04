from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/<slug:package_slug>/', views.CheckoutView.as_view(), name='checkout'),
    path('success/', views.PaymentSuccessView.as_view(), name='success'),
    path('webhook/', views.stripe_webhook, name='webhook'),
]

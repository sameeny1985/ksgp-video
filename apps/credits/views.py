from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import CreditPackage
class WalletView(LoginRequiredMixin, TemplateView):
    template_name = 'credits/wallet.html'
class PackageListView(ListView):
    model = CreditPackage
    template_name = 'credits/packages.html'
    queryset = CreditPackage.objects.filter(is_active=True)

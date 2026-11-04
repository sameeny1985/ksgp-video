from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .models import ContentReport


class ReportCreateView(LoginRequiredMixin, CreateView):
    model = ContentReport
    fields = ['reason', 'description', 'object_type', 'object_id']
    template_name = 'reports/form.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.reporter = self.request.user
        messages.success(self.request, _('Report submitted. Thank you.'))
        return super().form_valid(form)


class MyReportsView(LoginRequiredMixin, ListView):
    model = ContentReport
    template_name = 'reports/list.html'
    context_object_name = 'reports'
    paginate_by = 20

    def get_queryset(self):
        return ContentReport.objects.filter(reporter=self.request.user)

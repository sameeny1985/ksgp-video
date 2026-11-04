from apps.core.blockchain import append_block
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
import uuid
from .models import Channel
from .forms import ChannelForm

class ChannelListView(ListView):
    model = Channel
    template_name = 'channels/list.html'
    context_object_name = 'channels'
    paginate_by = 20
    def get_queryset(self):
        return Channel.objects.filter(status=Channel.Status.APPROVED, is_active=True).select_related('category', 'owner')

class ChannelDetailView(DetailView):
    model = Channel
    template_name = 'channels/detail.html'
    context_object_name = 'channel'
    slug_field = 'slug'
    def get_queryset(self):
        return Channel.objects.filter(status=Channel.Status.APPROVED, is_active=True)

class ChannelCreateView(LoginRequiredMixin, CreateView):
    model = Channel
    form_class = ChannelForm
    template_name = 'channels/form.html'
    success_url = reverse_lazy('dashboard:channels')
    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.owner = self.request.user
        obj.status = Channel.Status.PENDING
        base_slug = slugify(obj.name)[:150] or 'channel'
        obj.slug = f'{base_slug}-{uuid.uuid4().hex[:8]}'
        obj.save()
        messages.success(self.request, _('Channel submitted for review.'))
        try:
            append_block('channel_submit', actor=self.request.user, payload={'title': str(getattr(obj, 'name', getattr(obj, 'title', '')))}, object_type='channels', object_id=obj.pk)
        except Exception:
            pass
        try:
            from apps.notifications.services import create_notification
            create_notification(self.request.user, 'Channel submitted', f'Your channel "{obj.name}" is pending review.', 'info')
        except Exception:
            pass
        return super().form_valid(form)

class ChannelUpdateView(LoginRequiredMixin, UpdateView):
    model = Channel
    form_class = ChannelForm
    template_name = 'channels/form.html'
    success_url = reverse_lazy('dashboard:channels')
    def get_queryset(self):
        return Channel.objects.filter(owner=self.request.user)
    def form_valid(self, form):
        messages.success(self.request, _('Channel updated.'))
        return super().form_valid(form)

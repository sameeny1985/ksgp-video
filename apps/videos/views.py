from apps.core.blockchain import append_block
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from django.urls import reverse_lazy
from django.utils.text import slugify
import uuid
from .models import Video, SavedVideo
from .forms import VideoForm
from apps.core.models import Category
from apps.channels.models import Channel

class VideoListView(ListView):
    model = Video
    template_name = 'videos/list.html'
    context_object_name = 'videos'
    paginate_by = 24
    def get_queryset(self):
        qs = Video.objects.filter(status=Video.Status.APPROVED, is_active=True).select_related('channel', 'category')
        category = self.request.GET.get('category')
        language = self.request.GET.get('language')
        q = self.request.GET.get('q')
        if category:
            qs = qs.filter(category__slug=category)
        if language:
            qs = qs.filter(language=language)
        if q:
            qs = qs.filter(title__icontains=q)
        return qs.order_by('-is_featured', '-created_at')

class VideoSearchView(VideoListView):
    template_name = 'videos/list.html'

class CategoryVideosView(VideoListView):
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return super().get_queryset().filter(category=self.category)
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['category'] = self.category
        return ctx

class VideoDetailView(DetailView):
    model = Video
    template_name = 'videos/detail.html'
    context_object_name = 'video'
    slug_field = 'slug'
    def get_queryset(self):
        return Video.objects.filter(status=Video.Status.APPROVED, is_active=True).select_related('channel', 'category', 'owner')

class VideoCreateView(LoginRequiredMixin, CreateView):
    model = Video
    form_class = VideoForm
    template_name = 'videos/form.html'
    success_url = reverse_lazy('dashboard:videos')
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['channel'].queryset = Channel.objects.filter(owner=self.request.user, status=Channel.Status.APPROVED)
        return form
    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.owner = self.request.user
        obj.status = Video.Status.PENDING
        base_slug = slugify(obj.title)[:180] or 'video'
        obj.slug = f'{base_slug}-{uuid.uuid4().hex[:8]}'
        obj.save()
        messages.success(self.request, _('Video submitted for review.'))
        try:
            append_block('video_submit', actor=self.request.user, payload={'title': str(getattr(obj, 'name', getattr(obj, 'title', '')))}, object_type='videos', object_id=obj.pk)
        except Exception:
            pass
        try:
            from apps.notifications.services import create_notification
            create_notification(self.request.user, 'Video submitted', f'Your video "{obj.title}" is pending review.', 'info')
        except Exception:
            pass
        return super().form_valid(form)

class VideoUpdateView(LoginRequiredMixin, UpdateView):
    model = Video
    form_class = VideoForm
    template_name = 'videos/form.html'
    success_url = reverse_lazy('dashboard:videos')
    slug_field = 'slug'
    def get_queryset(self):
        return Video.objects.filter(owner=self.request.user)
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['channel'].queryset = Channel.objects.filter(owner=self.request.user)
        return form
    def form_valid(self, form):
        messages.success(self.request, _('Video updated.'))
        return super().form_valid(form)

def toggle_save(request, slug):
    if not request.user.is_authenticated:
        return redirect('account_login')
    video = get_object_or_404(Video, slug=slug, status=Video.Status.APPROVED)
    saved, created = SavedVideo.objects.get_or_create(user=request.user, video=video)
    if not created:
        saved.delete()
        messages.info(request, _('Removed from saved videos.'))
    else:
        messages.success(request, _('Video saved.'))
    return redirect(video.get_absolute_url())

def report_video(request, slug):
    messages.info(request, _('Report received. Thank you.'))
    return redirect('videos:detail', slug=slug)

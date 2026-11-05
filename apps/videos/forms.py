from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Video
from .youtube import fetch_youtube_meta, extract_youtube_id


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['youtube_url', 'channel', 'description', 'category', 'language']
        widgets = {
            'youtube_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.youtube.com/watch?v=...',
                'autocomplete': 'off',
            }),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'en'}),
            'channel': forms.Select(attrs={'class': 'form-select'}),
        }
        help_texts = {
            'youtube_url': _('Paste the YouTube link only. Title and thumbnail are taken from YouTube automatically.'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['youtube_url'].required = True

    def clean_youtube_url(self):
        url = self.cleaned_data.get('youtube_url', '').strip()
        if not extract_youtube_id(url):
            raise forms.ValidationError(_('Please enter a valid YouTube video URL.'))
        return url

    def clean(self):
        cleaned = super().clean()
        url = cleaned.get('youtube_url')
        if not url:
            return cleaned
        meta = fetch_youtube_meta(url)
        self._yt_meta = meta
        if not meta.get('video_id'):
            raise forms.ValidationError(_('Could not read this YouTube link.'))
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        meta = getattr(self, '_yt_meta', None) or fetch_youtube_meta(obj.youtube_url)
        if meta.get('video_id'):
            obj.youtube_video_id = meta['video_id']
        if meta.get('thumbnail_url'):
            obj.thumbnail_url = meta['thumbnail_url']
        # Always set title from YouTube on create; on edit refresh if empty
        if meta.get('title'):
            if not obj.pk or not obj.title:
                obj.title = meta['title'][:200]
            elif not obj.title:
                obj.title = meta['title'][:200]
        if not obj.title:
            obj.title = f"YouTube video {meta.get('video_id', '')}".strip()
        if commit:
            obj.save()
            self.save_m2m()
        return obj

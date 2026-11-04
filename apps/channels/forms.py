from django import forms
from .models import Channel

class ChannelForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['name', 'youtube_url', 'description', 'category', 'language', 'country']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'youtube_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.youtube.com/@channel'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'en'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'US'}),
        }

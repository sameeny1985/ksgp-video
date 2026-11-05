from django.views.generic import TemplateView
from django.shortcuts import redirect


class SafeSignupView(TemplateView):
    """Signup page without allauth SignupForm (avoids 500). Google-only."""
    template_name = 'account/signup.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/dashboard/')
        return super().dispatch(request, *args, **kwargs)


class SafeLoginView(TemplateView):
    """Styled login with Google primary + optional email via allauth login URL fallback."""
    template_name = 'account/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/dashboard/')
        return super().dispatch(request, *args, **kwargs)

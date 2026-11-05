from django.conf import settings


def site_settings(request):
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'KSGP Video'),
        'SITE_DESCRIPTION': getattr(settings, 'SITE_DESCRIPTION', ''),
        'SITE_URL': getattr(settings, 'SITE_URL', ''),
        'PLATFORM_VERSION': getattr(settings, 'PLATFORM_VERSION', '1.0.0'),
    }


def user_wallet(request):
    wallet = None
    try:
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            wallet = getattr(user, 'wallet', None)
    except Exception:
        wallet = None
    return {'user_wallet': wallet}

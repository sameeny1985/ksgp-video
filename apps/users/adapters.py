from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    def populate_username(self, request, user):
        # User model has no username field
        return

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        if not getattr(user, 'role', None):
            user.role = 'user'
        if commit:
            user.save()
        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.role = getattr(user, 'role', None) or 'user'
        # email-only user model
        email = data.get('email')
        if email:
            user.email = email
        first = data.get('first_name') or data.get('given_name') or ''
        last = data.get('last_name') or data.get('family_name') or ''
        if first:
            user.first_name = first[:150]
        if last:
            user.last_name = last[:150]
        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        return True

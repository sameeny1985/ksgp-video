from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import User, UserProfile
from apps.credits.models import CreditWallet


@receiver(post_save, sender=User)
def create_user_profile_and_wallet(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        CreditWallet.objects.get_or_create(user=instance)

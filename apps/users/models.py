"""
User models for KSGP Video Platform
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from apps.core.models import TimeStampedModel
import uuid


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model with email as username"""
    class Role(models.TextChoices):
        GUEST = 'guest', _('Guest')
        USER = 'user', _('Registered User')
        CREATOR = 'creator', _('Creator')
        ADVERTISER = 'advertiser', _('Advertiser')
        ADMIN = 'admin', _('Administrator')
        STAFF = 'staff', _('Staff')

    username = None  # Remove username field
    email = models.EmailField(_('email address'), unique=True, db_index=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER, db_index=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_email_verified = models.BooleanField(default=False)
    preferred_language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    country = models.CharField(max_length=2, blank=True, help_text='ISO 3166-1 alpha-2')
    phone = models.CharField(max_length=20, blank=True)
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(blank=True)
    banned_at = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    notification_preferences = models.JSONField(default=dict, blank=True)
    onboarding_completed = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return self.email

    @property
    def display_name(self):
        if hasattr(self, 'profile') and self.profile.display_name:
            return self.profile.display_name
        return self.email.split('@')[0]

    @property
    def is_creator(self):
        return self.role in [self.Role.CREATOR, self.Role.ADMIN, self.Role.STAFF]

    @property
    def is_advertiser(self):
        return self.role in [self.Role.ADVERTISER, self.Role.ADMIN, self.Role.STAFF]

    def has_role(self, role):
        return self.role == role or self.is_superuser


class UserProfile(TimeStampedModel):
    """Extended user profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/%Y/%m/', blank=True, null=True)
    website = models.URLField(blank=True)
    social_links = models.JSONField(default=dict, blank=True)  # {twitter, instagram, etc}
    location = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_public = models.BooleanField(default=True)
    show_email = models.BooleanField(default=False)
    creator_verified = models.BooleanField(default=False)
    advertiser_verified = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')

    def __str__(self):
        return f'Profile of {self.user.email}'


class UserFollow(TimeStampedModel):
    """Follow relationship between users/channels inside platform"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')

    class Meta:
        unique_together = ('follower', 'following')
        indexes = [
            models.Index(fields=['follower']),
            models.Index(fields=['following']),
        ]

    def __str__(self):
        return f'{self.follower} follows {self.following}'


class UserActivity(models.Model):
    """Track user activity for analytics and security"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=100)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'User activities'

    def __str__(self):
        return f'{self.user} - {self.action}'

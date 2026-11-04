import os
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import Category, Language, SystemSetting
from apps.credits.models import CreditPackage


class Command(BaseCommand):
    help = "Seed initial data and optional admin from ADMIN_EMAIL / ADMIN_PASSWORD env"

    def handle(self, *args, **options):
        self._seed_languages()
        self._seed_categories()
        self._seed_packages()
        self._seed_settings()
        self._seed_admin()
        self.stdout.write(self.style.SUCCESS("All seed data created successfully"))

    def _seed_admin(self):
        email = (os.environ.get("ADMIN_EMAIL") or "").strip()
        password = os.environ.get("ADMIN_PASSWORD") or ""
        if not email or not password:
            self.stdout.write(self.style.WARNING(
                "ADMIN_EMAIL / ADMIN_PASSWORD not set – skipping superuser"
            ))
            return
        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()
        if user:
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Superuser updated: {email}"))
            return
        user = User.objects.create_superuser(email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Superuser created: {email}"))

    def _seed_languages(self):
        langs = [
            ("en", "English", "English", False, 1),
            ("fr", "French", "Français", False, 2),
            ("fa", "Persian", "فارسی", True, 3),
            ("es", "Spanish", "Español", False, 4),
            ("de", "German", "Deutsch", False, 5),
            ("pt", "Portuguese", "Português", False, 6),
            ("ar", "Arabic", "العربية", True, 7),
            ("tr", "Turkish", "Türkçe", False, 8),
            ("ru", "Russian", "Русский", False, 9),
            ("zh-hans", "Chinese", "简体中文", False, 10),
            ("hi", "Hindi", "हिन्दी", False, 11),
            ("ja", "Japanese", "日本語", False, 12),
        ]
        for code, name, native, rtl, order in langs:
            Language.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "native_name": native,
                    "is_rtl": rtl,
                    "order": order,
                    "is_active": True,
                },
            )
        self.stdout.write(self.style.SUCCESS("Languages seeded"))

    def _seed_categories(self):
        cats = [
            ("Technology", "technology", "bi-cpu", "#3b82f6", 1),
            ("Programming", "programming", "bi-code-slash", "#8b5cf6", 2),
            ("Education", "education", "bi-book", "#10b981", 3),
            ("Gaming", "gaming", "bi-controller", "#ef4444", 4),
            ("Music", "music", "bi-music-note-beamed", "#ec4899", 5),
            ("Entertainment", "entertainment", "bi-film", "#f59e0b", 6),
            ("Finance", "finance", "bi-graph-up-arrow", "#14b8a6", 7),
            ("Business", "business", "bi-briefcase", "#6366f1", 8),
            ("Cryptocurrency", "cryptocurrency", "bi-currency-bitcoin", "#f97316", 9),
            ("Science", "science", "bi-flask", "#06b6d4", 10),
            ("Sports", "sports", "bi-trophy", "#84cc16", 11),
            ("Travel", "travel", "bi-airplane", "#0ea5e9", 12),
            ("Lifestyle", "lifestyle", "bi-heart", "#f43f5e", 13),
            ("News", "news", "bi-newspaper", "#64748b", 14),
            ("Health and Fitness", "health-fitness", "bi-heart-pulse", "#22c55e", 15),
            ("Other", "other", "bi-three-dots", "#94a3b8", 16),
        ]
        for name, slug, icon, color, order in cats:
            Category.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "icon": icon,
                    "color": color,
                    "order": order,
                    "is_featured": order <= 8,
                },
            )
        self.stdout.write(self.style.SUCCESS("Categories seeded"))

    def _seed_packages(self):
        packages = [
            ("Starter", "starter", "Perfect for new creators", Decimal("50.00"), Decimal("19.00"), Decimal("0"), 1),
            ("Basic", "basic", "For small channels", Decimal("120.00"), Decimal("39.00"), Decimal("10.00"), 2),
            ("Professional", "professional", "For active creators", Decimal("250.00"), Decimal("79.00"), Decimal("30.00"), 3),
            ("Business", "business", "For brands and agencies", Decimal("800.00"), Decimal("199.00"), Decimal("120.00"), 4),
        ]
        for name, slug, desc, credits, price, bonus, order in packages:
            CreditPackage.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": desc,
                    "credits": credits,
                    "price": price,
                    "bonus_credits": bonus,
                    "order": order,
                    "is_active": True,
                    "is_featured": slug == "professional",
                },
            )
        self.stdout.write(self.style.SUCCESS("Credit packages seeded"))

    def _seed_settings(self):
        SystemSetting.set("default_cpm_rate", "5.00", "float", "Default CPM rate in EUR")
        SystemSetting.set("default_cpc_rate", "0.25", "float", "Default CPC rate in EUR")
        SystemSetting.set("min_campaign_budget", "10.00", "float", "Minimum campaign budget")
        SystemSetting.set("ad_frequency_cap_daily", "5", "integer", "Default daily frequency cap")
        self.stdout.write(self.style.SUCCESS("System settings seeded"))

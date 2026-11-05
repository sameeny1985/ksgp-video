import os
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import Category, Language, SystemSetting
from apps.credits.models import CreditPackage


class Command(BaseCommand):
    help = "Seed data + admin from ADMIN_EMAIL / ADMIN_PASSWORD"

    def handle(self, *args, **options):
        self._langs(); self._cats(); self._packs(); self._settings(); self._admin()
        self.stdout.write(self.style.SUCCESS("Seed complete"))

    def _admin(self):
        email = (os.environ.get("ADMIN_EMAIL") or "").strip()
        password = os.environ.get("ADMIN_PASSWORD") or ""
        if not email or not password:
            self.stdout.write(self.style.WARNING("ADMIN_EMAIL/ADMIN_PASSWORD missing – skip admin"))
            return
        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()
        if user:
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Admin updated: {email}"))
        else:
            User.objects.create_superuser(email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Admin created: {email}"))

    def _langs(self):
        for code, name, native, rtl, order in [
            ("en","English","English",False,1),("fr","French","Français",False,2),
            ("fa","Persian","فارسی",True,3),("es","Spanish","Español",False,4),
            ("de","German","Deutsch",False,5),("pt","Portuguese","Português",False,6),
            ("ar","Arabic","العربية",True,7),("tr","Turkish","Türkçe",False,8),
            ("ru","Russian","Русский",False,9),("zh-hans","Chinese","简体中文",False,10),
            ("hi","Hindi","हिन्दी",False,11),("ja","Japanese","日本語",False,12),
        ]:
            Language.objects.get_or_create(code=code, defaults={"name":name,"native_name":native,"is_rtl":rtl,"order":order,"is_active":True})

    def _cats(self):
        for name, slug, icon, color, order in [
            ("Technology","technology","bi-cpu","#3b82f6",1),
            ("Programming","programming","bi-code-slash","#8b5cf6",2),
            ("Education","education","bi-book","#10b981",3),
            ("Gaming","gaming","bi-controller","#ef4444",4),
            ("Music","music","bi-music-note-beamed","#ec4899",5),
            ("Entertainment","entertainment","bi-film","#f59e0b",6),
            ("Business","business","bi-briefcase","#6366f1",7),
            ("Other","other","bi-three-dots","#94a3b8",8),
        ]:
            Category.objects.get_or_create(slug=slug, defaults={"name":name,"icon":icon,"color":color,"order":order,"is_featured":order<=6})

    def _packs(self):
        for name, slug, desc, credits, price, bonus, order in [
            ("Starter","starter","For new creators",Decimal("50"),Decimal("19"),Decimal("0"),1),
            ("Basic","basic","Small channels",Decimal("120"),Decimal("39"),Decimal("10"),2),
            ("Professional","professional","Active creators",Decimal("250"),Decimal("79"),Decimal("30"),3),
            ("Business","business","Brands",Decimal("800"),Decimal("199"),Decimal("120"),4),
        ]:
            CreditPackage.objects.get_or_create(slug=slug, defaults={"name":name,"description":desc,"credits":credits,"price":price,"bonus_credits":bonus,"order":order,"is_active":True,"is_featured":slug=="professional"})

    def _settings(self):
        SystemSetting.set("default_cpm_rate","5.00","float","Default CPM")
        SystemSetting.set("default_cpc_rate","0.25","float","Default CPC")

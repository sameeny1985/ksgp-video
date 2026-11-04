from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

class KSGPAdminSite(AdminSite):
    site_header = 'KSGP Video Administration'
    site_title = 'KSGP Video Admin'
    index_title = 'Platform Management Dashboard'

# We keep using default admin.site for simplicity, just customize titles in urls.py

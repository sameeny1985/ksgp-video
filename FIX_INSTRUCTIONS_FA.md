# اصلاح فوری Deploy برای KSGP Video

## مشکل اصلی فعلی
`ModuleNotFoundError: No module named 'apps.reports.urls'`

علت: پوشه `apps/reports/` فقط `apps.py` داشت و فایل‌های `urls.py` / `views.py` / `models.py` نداشت، در حالی که در `ksgp_video/urls.py` این خط وجود دارد:
`path('reports/', include('apps.reports.urls')),`

## کارهایی که باید در GitHub انجام دهید
1. محتویات پوشه `apps/reports/` این پچ را جایگزین/آپلود کنید (همه فایل‌ها).
2. فایل `apps/users/urls.py` را اضافه کنید (برای ایمنی import).
3. فایل `requirements.txt` را با نسخه سبک این پچ جایگزین کنید (اختیاری ولی توصیه‌شده).
4. Build Command رندر را به این تغییر دهید:

```
pip install -r requirements.txt && python manage.py makemigrations --noinput && python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py seed_data
```

دلیل `makemigrations`: در مخزن هیچ فایل migration واقعی (0001_initial.py) وجود ندارد؛ فقط `migrations/__init__.py` هست. بدون makemigrations جداول ساخته نمی‌شوند.

5. Environmentها را طبق README تنظیم کنید و دامنه را اضافه کنید:
   - ALLOWED_HOSTS=ksgp.onrender.com,.onrender.com
   - CSRF_TRUSTED_ORIGINS=https://ksgp.onrender.com
   - SITE_URL=https://ksgp.onrender.com

6. در settings.py اصلاحات ذکرشده در `ksgp_video/settings_PATCH_NOTES.txt` را اعمال کنید.

## payments/views.py
نسخه فعلی روی GitHub از نظر Indentation برای `_handle_checkout_completed` درست است و نیازی به حذف ندارد.

## سوپریوزر
بعد از اولین دیپلوی موفق در Shell رندر:
`python manage.py createsuperuser`
ایمیل ادمین همان چیزی است که خودتان وارد می‌کنید؛ از قبل hardcode نشده.

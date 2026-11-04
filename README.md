# KSGP Video

Default language: English. 12 languages configured.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| SECRET_KEY | Yes | Long random secret |
| DEBUG | Yes | False in production |
| ALLOWED_HOSTS | Yes | your-app.onrender.com |
| DATABASE_URL | Yes | Linked Render PostgreSQL |
| STRIPE_PUBLIC_KEY | Yes | pk_test_... / pk_live_... |
| STRIPE_SECRET_KEY | Yes | sk_test_... / sk_live_... |
| STRIPE_WEBHOOK_SECRET | Yes | whsec_... |
| SITE_URL | Yes | https://your-app.onrender.com |
| DEFAULT_FROM_EMAIL | Recommended | noreply@domain.com |
| EMAIL_HOST | Recommended | SMTP host |
| EMAIL_PORT | Recommended | 587 |
| EMAIL_HOST_USER | Recommended | SMTP user |
| EMAIL_HOST_PASSWORD | Recommended | SMTP password |
| EMAIL_BACKEND | Optional | django.core.mail.backends.smtp.EmailBackend |
| REDIS_URL | Optional | Cache / Celery |
| GOOGLE_CLIENT_ID | Optional | Google login |
| GOOGLE_CLIENT_SECRET | Optional | Google login |
| SENTRY_DSN | Optional | Error monitoring & alerts |
| YOUTUBE_API_KEY | Optional | Not required for core |
| CORS_ALLOWED_ORIGINS | Optional | Allowed origins |

Stripe webhook: `https://YOUR_APP/payments/webhook/`  
Event: `checkout.session.completed`

Health: `GET /health/` (database + cache status)

### Render
Build:
```
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py seed_data
```
Start:
```
gunicorn ksgp_video.wsgi:application --bind 0.0.0.0:$PORT
```

Logo: `static/images/ksgp_coin.png`

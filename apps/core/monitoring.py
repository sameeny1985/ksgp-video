"""
Lightweight production monitoring & alerting hooks.
Works with Sentry (if configured) and internal health signals.
"""
import logging
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger('apps.monitoring')


def capture_exception(exc, **kwargs):
    logger.exception('Captured exception: %s', exc)
    try:
        import sentry_sdk
        if getattr(settings, 'SENTRY_DSN', ''):
            sentry_sdk.capture_exception(exc)
    except Exception:
        pass


def capture_message(message, level='info', **kwargs):
    log = getattr(logger, level, logger.info)
    log(message)
    try:
        import sentry_sdk
        if getattr(settings, 'SENTRY_DSN', ''):
            sentry_sdk.capture_message(message, level=level)
    except Exception:
        pass


def record_metric(name, value=1, tags=None):
    """Simple in-process / cache metric counter for health dashboards"""
    key = f'metric:{name}:{timezone.now().strftime("%Y%m%d%H")}'
    try:
        current = cache.get(key, 0)
        cache.set(key, current + value, 3600 * 2)
    except Exception:
        pass
    logger.info('metric %s=%s tags=%s', name, value, tags or {})


def check_system_health():
    """Return dict of subsystem health for /health/ and ops"""
    from django.db import connection
    result = {'database': False, 'cache': False, 'time': timezone.now().isoformat()}
    try:
        connection.ensure_connection()
        result['database'] = True
    except Exception as e:
        capture_exception(e)
    try:
        cache.set('health_ping', '1', 10)
        result['cache'] = cache.get('health_ping') == '1'
    except Exception as e:
        capture_exception(e)
    result['ok'] = result['database']  # DB is critical
    return result


def alert_high_error_rate(threshold=50):
    """Example alert hook – count errors in last hour via cache metric"""
    key = f'metric:errors:{timezone.now().strftime("%Y%m%d%H")}'
    count = cache.get(key, 0)
    if count >= threshold:
        capture_message(f'High error rate: {count} errors this hour', level='error')
        return True
    return False

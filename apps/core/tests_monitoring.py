from django.test import TestCase, Client
from apps.core.monitoring import check_system_health, record_metric, capture_message

class MonitoringTests(TestCase):
    def test_health_dict(self):
        h = check_system_health()
        self.assertIn('database', h)
        self.assertIn('ok', h)

    def test_health_endpoint(self):
        c = Client()
        r = c.get('/health/')
        self.assertIn(r.status_code, [200, 503])
        self.assertIn('status', r.json())

    def test_record_metric_no_crash(self):
        record_metric('test_metric', 1)
        capture_message('test message', level='info')

from django.test import TestCase, Client
from apps.users.models import User

class AnalyticsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='an@example.com', password='StrongPass12345')

    def test_analytics_requires_login(self):
        r = self.client.get('/analytics/')
        self.assertIn(r.status_code, [301, 302])

    def test_analytics_authenticated(self):
        self.client.login(email='an@example.com', password='StrongPass12345')
        r = self.client.get('/analytics/')
        self.assertEqual(r.status_code, 200)

    def test_csv_export(self):
        self.client.login(email='an@example.com', password='StrongPass12345')
        r = self.client.get('/analytics/export/csv/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('text/csv', r['Content-Type'])

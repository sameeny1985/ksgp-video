"""Lightweight E2E-style flow tests (register path → dashboard → packages)"""
from decimal import Decimal
from django.test import TestCase, Client
from apps.users.models import User
from apps.credits.models import CreditPackage, CreditWallet

class E2EFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        CreditPackage.objects.create(
            name='Basic', slug='basic-e2e', credits=Decimal('100'),
            price=Decimal('39'), is_active=True
        )

    def test_home_to_packages_flow(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/credits/packages/').status_code, 200)
        self.assertEqual(self.client.get('/campaigns/pricing/').status_code, 200)
        self.assertEqual(self.client.get('/videos/').status_code, 200)

    def test_user_dashboard_flow(self):
        User.objects.create_user(email='e2e@example.com', password='StrongPass12345')
        self.assertTrue(self.client.login(email='e2e@example.com', password='StrongPass12345'))
        for path in ['/dashboard/', '/dashboard/channels/', '/dashboard/videos/',
                     '/dashboard/campaigns/', '/dashboard/wallet/', '/analytics/']:
            r = self.client.get(path)
            self.assertEqual(r.status_code, 200, msg=f'Failed: {path}')

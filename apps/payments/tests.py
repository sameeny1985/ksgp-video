from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from apps.users.models import User
from apps.credits.models import CreditPackage, CreditWallet
from apps.payments.models import Payment

class StripeCheckoutTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='stripe@example.com', password='StrongPass12345')
        self.package = CreditPackage.objects.create(
            name='Starter', slug='starter-test', credits=Decimal('50'),
            price=Decimal('19.00'), is_active=True
        )
        CreditWallet.objects.get_or_create(user=self.user)

    def test_packages_public(self):
        r = self.client.get('/credits/packages/')
        self.assertEqual(r.status_code, 200)

    def test_checkout_requires_auth(self):
        r = self.client.get(f'/payments/checkout/{self.package.slug}/')
        self.assertIn(r.status_code, [301, 302])

    @override_settings(STRIPE_SECRET_KEY='sk_test_dummy')
    @patch('apps.payments.views.stripe.checkout.Session.create')
    def test_checkout_creates_session(self, mock_create):
        mock_create.return_value = MagicMock(id='cs_test_123', url='https://checkout.stripe.com/test')
        self.client.login(email='stripe@example.com', password='StrongPass12345')
        r = self.client.get(f'/payments/checkout/{self.package.slug}/')
        # redirect to stripe
        self.assertIn(r.status_code, [302, 303])
        self.assertTrue(Payment.objects.filter(user=self.user, package=self.package).exists())

    def test_webhook_endpoint_accepts_post(self):
        r = self.client.post('/payments/webhook/', data=b'{}', content_type='application/json')
        # may be 400 without valid signature/body – should not 500
        self.assertIn(r.status_code, [200, 400])

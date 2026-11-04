from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User, UserProfile
from apps.credits.models import CreditWallet

class UserModelTests(TestCase):
    def test_create_user(self):
        u = User.objects.create_user(email='a@example.com', password='StrongPass12345')
        self.assertEqual(u.email, 'a@example.com')
        self.assertFalse(u.is_staff)
        self.assertTrue(u.check_password('StrongPass12345'))

    def test_create_superuser(self):
        u = User.objects.create_superuser(email='admin@example.com', password='StrongPass12345')
        self.assertTrue(u.is_staff)
        self.assertTrue(u.is_superuser)

class UserViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='u@example.com', password='StrongPass12345')

    def test_home_ok(self):
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_dashboard_redirects_anonymous(self):
        r = self.client.get('/dashboard/')
        self.assertIn(r.status_code, [301, 302])

    def test_dashboard_authenticated(self):
        self.client.login(email='u@example.com', password='StrongPass12345')
        r = self.client.get('/dashboard/')
        self.assertEqual(r.status_code, 200)

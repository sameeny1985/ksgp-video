from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.users.models import User
from apps.credits.models import CreditWallet, CreditTransaction

class WalletTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='w@example.com', password='StrongPass12345')
        self.wallet, _ = CreditWallet.objects.get_or_create(user=self.user)

    def test_credit_increases_balance(self):
        self.wallet.credit(Decimal('100'), description='Topup', source='purchase', idempotency_key='c1')
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('100'))

    def test_idempotent_credit(self):
        self.wallet.credit(Decimal('50'), description='A', source='purchase', idempotency_key='same')
        self.wallet.credit(Decimal('50'), description='B', source='purchase', idempotency_key='same')
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('50'))

    def test_available_balance(self):
        self.wallet.credit(Decimal('100'), description='T', source='purchase', idempotency_key='t1')
        self.wallet.reserved = Decimal('30')
        self.wallet.save()
        self.assertEqual(self.wallet.available_balance, Decimal('70'))

    def test_transaction_immutable(self):
        self.wallet.credit(Decimal('10'), description='X', source='purchase', idempotency_key='im1')
        tx = CreditTransaction.objects.filter(wallet=self.wallet).first()
        with self.assertRaises(Exception):
            tx.amount = Decimal('999')
            tx.save()

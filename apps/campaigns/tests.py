from decimal import Decimal
from django.test import TestCase, Client
from apps.users.models import User
from apps.campaigns.models import Campaign
from apps.credits.models import CreditWallet

class CampaignTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='c@example.com', password='StrongPass12345')
        self.wallet, _ = CreditWallet.objects.get_or_create(user=self.user)
        self.wallet.credit(Decimal('500'), description='Seed', source='purchase', idempotency_key='seed1')
        self.client = Client()

    def test_create_campaign_model(self):
        c = Campaign.objects.create(
            owner=self.user, name='Test', campaign_type=Campaign.Type.VIDEO_PROMOTION,
            ad_title='Title', ad_description='Desc', destination_url='https://youtube.com',
            budget=Decimal('50')
        )
        self.assertEqual(c.status, Campaign.Status.DRAFT)
        self.assertEqual(c.remaining_budget, Decimal('50'))

    def test_ctr_property(self):
        c = Campaign.objects.create(
            owner=self.user, name='CTR', campaign_type=Campaign.Type.VIDEO_PROMOTION,
            ad_title='T', ad_description='D', destination_url='https://youtube.com',
            budget=Decimal('10'), impressions=1000, clicks=50
        )
        self.assertEqual(float(c.ctr), 5.0)

    def test_campaign_list_requires_login(self):
        r = self.client.get('/campaigns/')
        self.assertIn(r.status_code, [301, 302])

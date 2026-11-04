from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from apps.users.models import User
from apps.campaigns.models import Campaign
from apps.credits.models import CreditWallet
from apps.ads.services import (
    get_eligible_campaigns, score_campaign, budget_pacing_ok, pick_ab_variant
)

class AdEngineAdvancedTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='ads2@example.com', password='StrongPass12345')
        w, _ = CreditWallet.objects.get_or_create(user=self.user)
        w.credit(Decimal('500'), description='seed', source='purchase', idempotency_key='ad2seed')
        self.campaign = Campaign.objects.create(
            owner=self.user, name='Paced', campaign_type=Campaign.Type.HOMEPAGE_FEATURED,
            status=Campaign.Status.ACTIVE, ad_title='Title A', ad_description='Desc A',
            destination_url='https://example.com', budget=Decimal('100'), reserved=Decimal('100'),
            daily_budget=Decimal('20'), pricing_model=Campaign.PricingModel.CPM,
            cpm_rate=Decimal('5.00'), notes='AB_B_TITLE: Title B\nAB_B_DESC: Desc B'
        )

    def test_score(self):
        self.assertGreater(score_campaign(self.campaign), 0)

    def test_pacing_allows_fresh(self):
        self.assertTrue(budget_pacing_ok(self.campaign))

    def test_ab_variant_stable(self):
        v1 = pick_ab_variant(self.campaign, session_key='sess1')
        v2 = pick_ab_variant(self.campaign, session_key='sess1')
        self.assertEqual(v1['variant'], v2['variant'])
        self.assertIn(v1['variant'], ('A', 'B'))

    def test_eligible_active(self):
        result = get_eligible_campaigns(limit=10)
        self.assertTrue(any(c.pk == self.campaign.pk for c in result))

    def test_paused_excluded(self):
        self.campaign.status = Campaign.Status.PAUSED
        self.campaign.save()
        result = get_eligible_campaigns(limit=10)
        self.assertFalse(any(c.pk == self.campaign.pk for c in result))

import stripe
import uuid
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.db import transaction
from django.utils import timezone

from apps.credits.models import CreditPackage, CreditWallet
from .models import Payment

# Pin API version that still allows payment_method_types=['card']
# This skips Stripe Link / phone code screen and goes to card form.
stripe.api_version = '2023-10-16'


def _stripe_ready():
    key = (getattr(settings, 'STRIPE_SECRET_KEY', None) or '').strip()
    if not key:
        return False, 'STRIPE_SECRET_KEY is empty'
    if not (key.startswith('sk_test_') or key.startswith('sk_live_')):
        return False, 'STRIPE_SECRET_KEY must start with sk_test_ or sk_live_'
    stripe.api_key = key
    return True, ''


def _sget(obj, key, default=None):
    if obj is None:
        return default
    try:
        if hasattr(obj, key):
            val = getattr(obj, key)
            if val is not None:
                return val
    except Exception:
        pass
    try:
        return obj[key]
    except Exception:
        pass
    try:
        return obj.to_dict().get(key, default)
    except Exception:
        return default


class CheckoutView(LoginRequiredMixin, View):
    def get(self, request, package_slug):
        package = get_object_or_404(CreditPackage, slug=package_slug, is_active=True)
        user = request.user

        ok, err = _stripe_ready()
        if not ok:
            messages.error(request, f'Payment config error: {err}')
            return redirect('credits:packages')

        total_credits = package.credits + (package.bonus_credits or Decimal('0'))
        idempotency_key = f'checkout-{user.id}-{package.slug}-{uuid.uuid4().hex[:12]}'

        payment = Payment.objects.create(
            user=user,
            package=package,
            amount=package.price,
            currency=(package.currency or 'EUR').upper(),
            status=Payment.Status.PENDING,
            credits_granted=total_credits,
            description=f'Purchase of {package.name}',
            idempotency_key=idempotency_key,
        )

        try:
            success_url = (
                request.build_absolute_uri(reverse('payments:success'))
                + '?session_id={CHECKOUT_SESSION_ID}'
            )
            cancel_url = request.build_absolute_uri(reverse('credits:packages'))
            unit_amount = int(Decimal(package.price) * 100)

            session = stripe.checkout.Session.create(
                mode='payment',
                payment_method_types=['card'],  # card only – no Link / Bancontact
                customer_email=user.email,
                line_items=[{
                    'price_data': {
                        'currency': (package.currency or 'eur').lower(),
                        'product_data': {
                            'name': f'KSGP Credits – {package.name}',
                            'description': f'{total_credits} advertising credits',
                        },
                        'unit_amount': unit_amount,
                    },
                    'quantity': 1,
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'payment_id': str(payment.id),
                    'user_id': str(user.id),
                    'package_slug': package.slug,
                    'credits': str(total_credits),
                },
            )

            payment.stripe_checkout_session_id = session.id
            payment.save(update_fields=['stripe_checkout_session_id'])
            return redirect(session.url, code=303)

        except Exception as e:
            payment.status = Payment.Status.FAILED
            payment.failure_reason = str(e)[:500]
            payment.save(update_fields=['status', 'failure_reason'])
            messages.error(request, f'Payment failed: {e}')
            return redirect('credits:packages')


class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/success.html'

    def get(self, request, *args, **kwargs):
        session_id = request.GET.get('session_id')
        self.credited_amount = Decimal('0')
        self.paid = False
        self.fulfill_error = ''

        if session_id:
            ok, err = _stripe_ready()
            if ok:
                try:
                    session = stripe.checkout.Session.retrieve(session_id)
                    payment_status = str(_sget(session, 'payment_status') or '').lower()
                    status = str(_sget(session, 'status') or '').lower()
                    self.paid = payment_status in ('paid', 'no_payment_required') or status == 'complete'
                    # Always try fulfill when session is complete/paid
                    if self.paid or status in ('complete', 'open'):
                        amount, err2 = fulfill_payment_for_session(session, user=request.user)
                        self.credited_amount = amount or Decimal('0')
                        if amount and amount > 0:
                            self.paid = True
                        if err2:
                            self.fulfill_error = err2
                except Exception as e:
                    self.fulfill_error = str(e)
            else:
                self.fulfill_error = err

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['session_id'] = self.request.GET.get('session_id')
        ctx['paid'] = getattr(self, 'paid', False)
        ctx['credited_amount'] = getattr(self, 'credited_amount', Decimal('0'))
        ctx['fulfill_error'] = getattr(self, 'fulfill_error', '')
        try:
            wallet = CreditWallet.objects.filter(user=self.request.user).first()
            ctx['wallet_balance'] = wallet.balance if wallet else Decimal('0')
        except Exception:
            ctx['wallet_balance'] = None
        return ctx


@csrf_exempt
def stripe_webhook(request):
    ok, _ = _stripe_ready()
    if not ok:
        return HttpResponse(status=500)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    endpoint_secret = (getattr(settings, 'STRIPE_WEBHOOK_SECRET', None) or '').strip()

    if not endpoint_secret:
        try:
            import json
            event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
        except Exception:
            return HttpResponse(status=400)
    else:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except Exception:
            return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        fulfill_payment_for_session(event['data']['object'], user=None)
    return HttpResponse(status=200)


def fulfill_payment_for_session(session, user=None):
    """
    Find Payment and credit wallet.
    Returns (credited_amount, error_string).
    """
    metadata = _sget(session, 'metadata') or {}
    try:
        if hasattr(metadata, 'to_dict'):
            metadata = metadata.to_dict()
        elif not isinstance(metadata, dict):
            metadata = dict(metadata)
    except Exception:
        metadata = {}

    payment = None
    payment_id = metadata.get('payment_id') if isinstance(metadata, dict) else None
    session_id = _sget(session, 'id')

    if payment_id:
        payment = Payment.objects.filter(id=payment_id).first()

    if payment is None and session_id:
        payment = Payment.objects.filter(stripe_checkout_session_id=session_id).first()

    # Last resort: latest pending payment for this user
    if payment is None and user is not None:
        payment = (
            Payment.objects
            .filter(user=user, status=Payment.Status.PENDING)
            .order_by('-created_at')
            .first()
        )

    if payment is None:
        return Decimal('0'), 'Payment record not found for this session'

    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(id=payment.id)

            if payment.status == Payment.Status.SUCCEEDED:
                # Already done – return existing credit amount
                return payment.credits_granted or Decimal('0'), ''

            payment.status = Payment.Status.SUCCEEDED
            pi = _sget(session, 'payment_intent')
            if pi:
                payment.stripe_payment_intent_id = str(pi)
            if session_id:
                payment.stripe_checkout_session_id = str(session_id)
            payment.credits_granted_at = timezone.now()

            credits = payment.credits_granted or Decimal('0')
            if credits <= 0 and payment.package_id:
                pkg = payment.package
                credits = (pkg.credits or Decimal('0')) + (pkg.bonus_credits or Decimal('0'))
                payment.credits_granted = credits
            payment.save()

            if credits <= 0:
                return Decimal('0'), 'Payment succeeded but credits amount is 0'

            wallet, _ = CreditWallet.objects.select_for_update().get_or_create(user=payment.user)
            wallet.credit(
                amount=credits,
                description=f'Purchase: {payment.package.name if payment.package else "Credits"}',
                source='purchase',
                idempotency_key=f'stripe-{payment.id}',
                payment=payment,
            )
            # refresh
            wallet.refresh_from_db()
            return credits, ''
    except Exception as e:
        return Decimal('0'), str(e)

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
from django.utils.decorators import method_decorator
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils import timezone

from apps.credits.models import CreditPackage, CreditWallet
from .models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


class CheckoutView(LoginRequiredMixin, View):
    """Create Stripe Checkout Session for a credit package"""

    def get(self, request, package_slug):
        package = get_object_or_404(CreditPackage, slug=package_slug, is_active=True)
        user = request.user

        # Create pending payment record
        idempotency_key = f'checkout-{user.id}-{package.slug}-{uuid.uuid4().hex[:12]}'
        payment = Payment.objects.create(
            user=user,
            package=package,
            amount=package.price,
            currency=package.currency or 'EUR',
            status=Payment.Status.PENDING,
            credits_granted=package.total_credits,
            description=f'Purchase of {package.name}',
            idempotency_key=idempotency_key,
        )

        try:
            success_url = request.build_absolute_uri(reverse('payments:success')) + '?session_id={CHECKOUT_SESSION_ID}'
            cancel_url = request.build_absolute_uri(reverse('credits:packages'))

            session = stripe.checkout.Session.create(
                mode='payment',
                customer_email=user.email,
                line_items=[{
                    'price_data': {
                        'currency': (package.currency or 'eur').lower(),
                        'product_data': {
                            'name': f'KSGP Video Credits – {package.name}',
                            'description': f'{package.total_credits} advertising credits',
                        },
                        'unit_amount': int(package.price * 100),  # cents
                    },
                    'quantity': 1,
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'payment_id': str(payment.id),
                    'user_id': str(user.id),
                    'package_slug': package.slug,
                    'credits': str(package.total_credits),
                },
                idempotency_key=idempotency_key,
            )

            payment.stripe_checkout_session_id = session.id
            payment.save(update_fields=['stripe_checkout_session_id'])

            return redirect(session.url, code=303)

        except Exception as e:
            payment.status = Payment.Status.FAILED
            payment.failure_reason = str(e)
            payment.save(update_fields=['status', 'failure_reason'])
            messages.error(request, _('Payment initiation failed. Please try again.'))
            return redirect('credits:packages')


class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/success.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        session_id = self.request.GET.get('session_id')
        ctx['session_id'] = session_id
        if session_id:
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                ctx['paid'] = session.payment_status == 'paid'
            except Exception:
                ctx['paid'] = False
        return ctx


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks – credit wallet on successful payment"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    if not endpoint_secret:
        # In development without webhook secret we still try to process
        event = None
        try:
            event = stripe.Event.construct_from(
                __import__('json').loads(payload), stripe.api_key
            )
        except Exception:
            return HttpResponse(status=400)
    else:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        _handle_checkout_completed(session)
    elif event['type'] == 'payment_intent.succeeded':
        # Fallback handling if needed
        pass

    return HttpResponse(status=200)


def _handle_checkout_completed(session):
    """Credit the user wallet atomically"""
    metadata = session.get('metadata') or {}
    payment_id = metadata.get('payment_id')
    if not payment_id:
        return
    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(id=payment_id)
            if payment.status == Payment.Status.SUCCEEDED:
                return  # already processed (idempotent)

            payment.status = Payment.Status.SUCCEEDED
            payment.stripe_payment_intent_id = session.get('payment_intent') or ''
            payment.credits_granted_at = timezone.now()
            payment.save()

            wallet, _ = CreditWallet.objects.select_for_update().get_or_create(user=payment.user)
            credits = payment.credits_granted or Decimal('0')

            if credits > 0:
                wallet.credit(
                    amount=credits,
                    description=f'Purchase: {payment.package.name if payment.package else "Credits"}',
                    source='purchase',
                    idempotency_key=f'stripe-{payment.id}',
                    payment=payment,
                )

                try:
                    from apps.notifications.services import notify_payment_success
                    notify_payment_success(payment.user, payment.amount, credits)
                except Exception as notification_error:
                    print(f'Payment notification error: {notification_error}')

    except Payment.DoesNotExist:
        pass
    except Exception as e:
        # Log in real deployment
        print(f'Webhook error: {e}')


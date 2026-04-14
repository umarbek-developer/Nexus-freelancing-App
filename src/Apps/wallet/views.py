"""
Wallet views — balance overview + withdrawal system (#13).
"""
import logging
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from .models import Wallet, Withdrawal

logger = logging.getLogger(__name__)


@login_required
def wallet_overview(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    transactions = wallet.transactions.all()[:20]
    withdrawals  = wallet.withdrawals.all()[:10]
    pending_withdrawals_total = sum(
        w.amount for w in wallet.withdrawals.filter(status=Withdrawal.PENDING)
    )
    return render(request, 'wallet.html', {
        'wallet':                   wallet,
        'transactions':             transactions,
        'withdrawals':              withdrawals,
        'pending_withdrawals_total': pending_withdrawals_total,
    })


@login_required
def withdrawal_request(request):
    """Freelancer requests to withdraw available balance."""
    if request.user.role != 'freelancer':
        messages.error(request, 'Faqat freelancerlar pul yechib olishi mumkin.')
        return redirect('dashboard')

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        destination = request.POST.get('destination', '').strip()
        method      = request.POST.get('method', 'bank_transfer')

        try:
            amount = Decimal(request.POST.get('amount', '0').strip())
        except InvalidOperation:
            messages.error(request, 'Noto\'g\'ri summa.')
            return redirect('withdrawal_request')

        if amount <= 0:
            messages.error(request, 'Summa musbat bo\'lishi kerak.')
            return redirect('withdrawal_request')

        if amount > wallet.balance:
            messages.error(
                request,
                f'Hisobingizda yetarli mablag\' yo\'q. Mavjud: ${wallet.balance}',
            )
            return redirect('withdrawal_request')

        if not destination:
            messages.error(request, 'Qabul qiluvchi manzilni kiriting.')
            return redirect('withdrawal_request')

        Withdrawal.objects.create(
            wallet=wallet,
            amount=amount,
            method=method,
            destination=destination,
            status=Withdrawal.PENDING,
        )
        logger.info(
            'Withdrawal requested: user=%s amount=%s method=%s',
            request.user.pk, amount, method,
        )
        messages.success(
            request,
            f'${amount} yechib olish so\'rovi yuborildi. Admin ko\'rib chiqadi.',
        )
        return redirect('wallet_overview')

    return render(request, 'withdrawal-request.html', {'wallet': wallet})

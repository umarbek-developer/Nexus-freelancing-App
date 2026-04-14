"""
Contract views.

Fixes:
  #17 — select_related on all queries
  #18 — pagination on contract list

Features:
  #14 — dispute system (open dispute on active contract)
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from Apps.wallet.models import Wallet
from .models import Contract, Dispute
from Apps.reviews.models import Review

logger = logging.getLogger(__name__)


@login_required
def my_contracts(request):
    if request.user.role == 'freelancer':
        qs = Contract.objects.filter(freelancer=request.user)
    else:
        qs = Contract.objects.filter(client=request.user)

    qs = qs.select_related('job', 'client', 'freelancer').order_by('-created_at')  # #17

    # #18: pagination
    paginator = Paginator(qs, 20)
    page      = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'contracts.html', {'contracts': page})


@login_required
def contract_detail(request, pk):
    contract = get_object_or_404(
        Contract.objects.select_related('job', 'client', 'freelancer'),  # #17
        pk=pk,
    )
    if contract.client != request.user and contract.freelancer != request.user:
        return redirect('landing_page')

    reviews         = Review.objects.filter(contract=contract).select_related('reviewer')
    already_reviewed = Review.objects.filter(contract=contract, reviewer=request.user).exists()
    open_dispute    = contract.disputes.filter(status=Dispute.OPEN).first()

    return render(request, 'contract-detail.html', {
        'contract':         contract,
        'reviews':          reviews,
        'already_reviewed': already_reviewed,
        'open_dispute':     open_dispute,
    })


@login_required
def complete_contract(request, pk):
    contract = get_object_or_404(
        Contract.objects.select_related('job', 'client', 'freelancer'),
        pk=pk,
    )
    if contract.client != request.user:
        return redirect('client_dashboard')

    if request.method != 'POST':
        return redirect('contract_detail', pk=contract.pk)

    if contract.status == 'completed':
        messages.error(request, 'Bu shartnoma allaqachon yakunlangan.')
        return redirect('contract_detail', pk=contract.pk)

    if contract.status != 'active':
        messages.error(request, 'Faqat faol shartnomalarni yakunlash mumkin.')
        return redirect('contract_detail', pk=contract.pk)

    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(user=contract.freelancer)
        Contract.objects.filter(pk=contract.pk).update(status='completed')
        contract.job.status = 'completed'
        contract.job.save(update_fields=['status'])
        wallet.credit(
            amount=contract.amount,
            description=f'Shartnoma #{contract.pk} uchun to\'lov: {contract.job.title}',
        )

    logger.info(
        'Contract completed: contract=%s client=%s freelancer=%s amount=%s',
        contract.pk, contract.client_id, contract.freelancer_id, contract.amount,
    )
    messages.success(
        request,
        f'Shartnoma yakunlandi. ${contract.amount} freelancer hisobiga o\'tkazildi.',
    )
    return redirect('contract_detail', pk=contract.pk)


# ── Feature #14: Dispute system ───────────────────────────────────────────────

@login_required
def open_dispute(request, pk):
    """Either party can open a dispute on an active contract."""
    contract = get_object_or_404(
        Contract.objects.select_related('client', 'freelancer'),
        pk=pk,
    )

    if contract.client != request.user and contract.freelancer != request.user:
        return redirect('landing_page')

    if contract.status not in ('active',):
        messages.error(request, 'Faqat faol shartnomalar uchun nizo ochish mumkin.')
        return redirect('contract_detail', pk=contract.pk)

    # Prevent duplicate open disputes
    if contract.disputes.filter(status=Dispute.OPEN).exists():
        messages.info(request, 'Bu shartnoma bo\'yicha nizo allaqachon ochilgan.')
        return redirect('contract_detail', pk=contract.pk)

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if len(reason) < 20:
            messages.error(request, 'Nizo sababi kamida 20 belgidan iborat bo\'lishi kerak.')
            return render(request, 'dispute-form.html', {'contract': contract})

        Dispute.objects.create(
            contract=contract,
            opened_by=request.user,
            reason=reason,
            status=Dispute.OPEN,
        )
        # Mark contract as disputed
        Contract.objects.filter(pk=contract.pk).update(status='disputed')

        logger.info(
            'Dispute opened: contract=%s by=%s',
            contract.pk, request.user.pk,
        )
        messages.success(
            request,
            'Nizo ochildi. Admin tez orada ko\'rib chiqadi.',
        )
        return redirect('contract_detail', pk=contract.pk)

    return render(request, 'dispute-form.html', {'contract': contract})

"""
Review views.

Fix #7 — rating: prevent ValueError on non-numeric input, validate 1–5 range.
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from Apps.contracts.models import Contract
from .models import Review

logger = logging.getLogger(__name__)


@login_required
def leave_review(request, contract_pk):
    contract = get_object_or_404(
        Contract.objects.select_related('client', 'freelancer', 'job'),
        pk=contract_pk,
    )

    if contract.client != request.user and contract.freelancer != request.user:
        return redirect('dashboard')

    if contract.status != 'completed':
        messages.error(request, 'Izoh qoldirish uchun shartnoma yakunlangan bo\'lishi kerak.')
        return redirect('contract_detail', pk=contract.pk)

    already_reviewed = Review.objects.filter(contract=contract, reviewer=request.user).exists()
    if already_reviewed:
        messages.info(request, 'Siz allaqachon izoh qoldirdingiz.')
        return redirect('contract_detail', pk=contract.pk)

    reviewee = contract.freelancer if request.user == contract.client else contract.client

    if request.method == 'POST':
        # #7: safe int conversion — no ValueError crash
        try:
            rating = int(request.POST.get('rating', 5))
        except (ValueError, TypeError):
            rating = 5

        # Clamp to valid range
        rating  = max(1, min(5, rating))
        comment = (request.POST.get('comment') or '').strip()

        if not comment:
            messages.error(request, 'Izoh matni bo\'sh bo\'lmasin.')
            return render(request, 'leave-review.html', {'contract': contract})

        Review.objects.create(
            contract=contract,
            reviewer=request.user,
            reviewee=reviewee,
            rating=rating,
            comment=comment,
        )
        logger.info(
            'Review created: contract=%s reviewer=%s rating=%s',
            contract.pk, request.user.pk, rating,
        )
        messages.success(request, 'Izoh saqlandi.')
        return redirect('contract_detail', pk=contract.pk)

    return render(request, 'leave-review.html', {'contract': contract})

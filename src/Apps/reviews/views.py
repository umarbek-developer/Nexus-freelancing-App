from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from Apps.contracts.models import Contract
from .models import Review


@login_required
def leave_review(request, contract_pk):
    contract = get_object_or_404(Contract, pk=contract_pk)
    if contract.client != request.user and contract.freelancer != request.user:
        return redirect("dashboard")

    if contract.status != "completed":
        messages.error(request, "Izoh qoldirish uchun shartnoma yakunlangan bo‘lishi kerak.")
        return redirect("contract_detail", pk=contract.pk)

    if request.user == contract.client:
        reviewee = contract.freelancer
    else:
        reviewee = contract.client

    existing = Review.objects.filter(contract=contract, reviewer=request.user).first()
    if existing:
        return redirect("contract_detail", pk=contract.pk)

    if request.method == "POST":
        rating = int(request.POST.get("rating") or 5)
        comment = (request.POST.get("comment") or "").strip()
        if not comment:
            messages.error(request, "Izoh matni bo‘sh bo‘lmasin.")
            return redirect("leave_review", contract_pk=contract.pk)

        if rating < 1:
            rating = 1
        if rating > 5:
            rating = 5

        Review.objects.create(
            contract=contract,
            reviewer=request.user,
            reviewee=reviewee,
            rating=rating,
            comment=comment,
        )
        messages.success(request, "Izoh saqlandi.")
        return redirect("contract_detail", pk=contract.pk)

    return render(request, "leave-review.html", {"contract": contract})
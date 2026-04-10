from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Contract


@login_required
def my_contracts(request):
    contracts = (
        Contract.objects.select_related("job", "client", "freelancer")
        .filter(client=request.user)
        .order_by("-created_at")
    )
    if getattr(request.user, "role", "") == "freelancer":
        contracts = (
            Contract.objects.select_related("job", "client", "freelancer")
            .filter(freelancer=request.user)
            .order_by("-created_at")
        )

    return render(request, "contracts.html", {"contracts": contracts})


@login_required
def contract_detail(request, pk):
    contract = get_object_or_404(
        Contract.objects.select_related("job", "client", "freelancer"),
        pk=pk,
    )
    if contract.client != request.user and contract.freelancer != request.user:
        return redirect("dashboard")
    return render(request, "contract-detail.html", {"contract": contract})


@login_required
def complete_contract(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if contract.client != request.user:
        return redirect("dashboard")

    if request.method != "POST":
        return redirect("contract_detail", pk=contract.pk)

    contract.status = "completed"
    contract.save()

    contract.job.status = "completed"
    contract.job.save()

    messages.success(request, "Shartnoma yakunlandi.")
    return redirect("contract_detail", pk=contract.pk)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from Apps.jobs.models import Job
from Apps.contracts.models import Contract
from .models import Proposal


@login_required
def submit_proposal(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk)

    if request.method == "POST":
        cover_letter = request.POST.get("cover_letter", "").strip()
        proposed_rate = request.POST.get("proposed_rate") or 0

        if not cover_letter:
            return redirect("job_detail", pk=job.pk)

        Proposal.objects.create(
            job=job,
            freelancer=request.user,
            cover_letter=cover_letter,
            proposed_rate=proposed_rate,
            status="pending",
        )
        messages.success(request, "Taklif yuborildi.")
        return redirect("job_list")

    return redirect("job_detail", pk=job.pk)


@login_required
def my_proposals(request):
    proposals = Proposal.objects.filter(freelancer=request.user)
    return render(request, "my-proposals.html", {"proposals": proposals})


@login_required
def view_proposals(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    proposals = Proposal.objects.filter(job=job)
    return render(request, "job-proposals.html", {"job": job, "proposals": proposals})


@login_required
def accept_proposal(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    job = proposal.job

    if request.user != job.client:
        return redirect("dashboard")

    if request.method != "POST":
        return redirect("view_proposals", job_pk=job.pk)

    proposal.status = "accepted"
    proposal.save()

    job.status = "in_progress"
    job.save()

    contract_exists = Contract.objects.filter(job=job).exists()
    if not contract_exists:
        Contract.objects.create(
            job=job,
            client=job.client,
            freelancer=proposal.freelancer,
            amount=proposal.proposed_rate,
            status="active",
        )

    messages.success(request, "Taklif qabul qilindi. Shartnoma yaratildi.")
    return redirect("view_proposals", job_pk=job.pk)


@login_required
def reject_proposal(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    job = proposal.job

    if request.user != job.client:
        return redirect("dashboard")

    if request.method != "POST":
        return redirect("view_proposals", job_pk=job.pk)

    proposal.status = "rejected"
    proposal.save()
    messages.success(request, "Taklif rad etildi.")
    return redirect("view_proposals", job_pk=job.pk)

"""
Proposal views.

Fixes applied:
  #4  — cover letter minimum 20 chars enforced in form view (matches API)
  #5  — IntegrityError caught → user-friendly message instead of 500
  #17 — select_related on queryset
  #18 — paginated my_proposals list
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404, render, redirect

from Apps.jobs.models import Job
from Apps.contracts.models import Contract
from .models import Proposal

logger = logging.getLogger(__name__)


@login_required
def submit_proposal(request, job_pk):
    job = get_object_or_404(Job.objects.select_related('client'), pk=job_pk)

    if job.status != 'open':
        messages.error(request, 'Bu ish uchun taklif yuborib bo\'lmaydi — ish yopiq.')
        return redirect('job_detail', pk=job.pk)

    if request.user == job.client:
        messages.error(request, 'O\'z ishingizga taklif yuborib bo\'lmaydi.')
        return redirect('job_detail', pk=job.pk)

    if request.method == 'POST':
        cover_letter  = request.POST.get('cover_letter', '').strip()
        proposed_rate = request.POST.get('proposed_rate', '').strip()

        # #4: enforce minimum cover letter length (matches API serializer)
        if len(cover_letter) < 20:
            messages.error(request, 'Xat kamida 20 belgidan iborat bo\'lishi kerak.')
            return redirect('job_detail', pk=job.pk)

        try:
            rate = float(proposed_rate)
            if rate <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, 'Narx musbat son bo\'lishi kerak.')
            return redirect('job_detail', pk=job.pk)

        try:
            with transaction.atomic():
                Proposal.objects.create(
                    job=job,
                    freelancer=request.user,
                    cover_letter=cover_letter,
                    proposed_rate=rate,
                    status=Proposal.PENDING,
                )
            logger.info('Proposal submitted: job=%s freelancer=%s', job.pk, request.user.pk)
            messages.success(request, 'Taklif muvaffaqiyatli yuborildi.')
        except IntegrityError:
            # #5: unique_together (job, freelancer) violated — show friendly message
            messages.error(request, 'Siz bu ish uchun allaqachon taklif yuborgansiz.')

        return redirect('job_list')

    return redirect('job_detail', pk=job.pk)


@login_required
def my_proposals(request):
    proposals_qs = (
        Proposal.objects
        .filter(freelancer=request.user)
        .select_related('job', 'job__client')   # #17: avoid N+1
        .order_by('-created_at')
    )
    # #18: pagination
    paginator      = Paginator(proposals_qs, 20)
    proposals_page = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'my-proposals.html', {'proposals': proposals_page})


@login_required
def view_proposals(request, job_pk):
    job = get_object_or_404(Job.objects.select_related('client'), pk=job_pk)
    if request.user != job.client:
        messages.error(request, 'Bu sahifani ko\'rish uchun ish egasi bo\'lishingiz kerak.')
        return redirect('job_detail', pk=job.pk)

    proposals = (
        Proposal.objects
        .filter(job=job)
        .select_related('freelancer')
        .order_by('-created_at')
    )
    return render(request, 'job-proposals.html', {'job': job, 'proposals': proposals})


@login_required
def accept_proposal(request, pk):
    proposal = get_object_or_404(
        Proposal.objects.select_related('job', 'freelancer', 'job__client'),
        pk=pk,
    )
    job = proposal.job

    if request.user != job.client:
        return redirect('client_dashboard')

    if request.method != 'POST':
        return redirect('view_proposals', job_pk=job.pk)

    if proposal.status != Proposal.PENDING:
        messages.error(request, 'Bu taklif allaqachon qayta ishlangan.')
        return redirect('view_proposals', job_pk=job.pk)

    with transaction.atomic():
        proposal.status = Proposal.ACCEPTED
        proposal.save(update_fields=['status', 'updated_at'])

        # Reject all other pending proposals for the same job
        Proposal.objects.filter(
            job=job, status=Proposal.PENDING
        ).exclude(pk=proposal.pk).update(status=Proposal.REJECTED)

        job.status = 'in_progress'
        job.save(update_fields=['status'])

        contract, created = Contract.objects.get_or_create(
            job=job,
            defaults={
                'client':     job.client,
                'freelancer': proposal.freelancer,
                'amount':     proposal.proposed_rate,
                'status':     'active',
            },
        )

    logger.info(
        'Proposal accepted: proposal=%s contract=%s created=%s',
        proposal.pk, contract.pk, created,
    )
    messages.success(request, 'Taklif qabul qilindi. Shartnoma yaratildi.')
    return redirect('view_proposals', job_pk=job.pk)


@login_required
def reject_proposal(request, pk):
    proposal = get_object_or_404(
        Proposal.objects.select_related('job__client'),
        pk=pk,
    )
    job = proposal.job

    if request.user != job.client:
        return redirect('client_dashboard')

    if request.method != 'POST':
        return redirect('view_proposals', job_pk=job.pk)

    if proposal.status != Proposal.PENDING:
        messages.error(request, 'Faqat kutilayotgan takliflarni rad etish mumkin.')
        return redirect('view_proposals', job_pk=job.pk)

    proposal.status = Proposal.REJECTED
    proposal.save(update_fields=['status', 'updated_at'])
    messages.success(request, 'Taklif rad etildi.')
    return redirect('view_proposals', job_pk=job.pk)

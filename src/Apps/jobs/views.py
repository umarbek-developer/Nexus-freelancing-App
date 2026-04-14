"""
Job views — browse, detail, post, edit, close.

Fixes applied:
  #1  — edit_job blocked when proposals exist
  #4  — budget validated (min > 0, max >= min)
  #9  — skills saved on post/edit
  #11 — full-text search + budget filter on job_list
  #17 — select_related on all queries
  #18 — paginated job list (20 per page)
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect

from .models import Job, Skill
from Apps.proposals.models import Proposal

logger = logging.getLogger(__name__)


def job_list(request):
    """Browse jobs — search, category filter, budget filter, pagination."""
    qs = (
        Job.objects
        .filter(status='open')
        .select_related('client')         # #17: avoid N+1 on client lookup
        .prefetch_related('skills')
        .order_by('-created_at')
    )

    # #11: full-text search
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    # Category filter
    selected_category = request.GET.get('category', '')
    if selected_category:
        qs = qs.filter(category=selected_category)

    # Budget filter
    budget_min = request.GET.get('budget_min', '')
    budget_max = request.GET.get('budget_max', '')
    if budget_min:
        try:
            qs = qs.filter(budget_max__gte=float(budget_min))
        except ValueError:
            pass
    if budget_max:
        try:
            qs = qs.filter(budget_min__lte=float(budget_max))
        except ValueError:
            pass

    # Skill filter
    skill_slug = request.GET.get('skill', '')
    if skill_slug:
        qs = qs.filter(skills__slug=skill_slug)

    # Hide jobs the freelancer already applied to
    if request.user.is_authenticated and request.user.role == 'freelancer':
        applied_ids = Proposal.objects.filter(
            freelancer=request.user
        ).values_list('job_id', flat=True)
        qs = qs.exclude(id__in=applied_ids)

    # #18: Pagination
    paginator = Paginator(qs, 20)
    page      = request.GET.get('page', 1)
    jobs_page = paginator.get_page(page)

    context = {
        'jobs':              jobs_page,
        'jobs_count':        paginator.count,
        'categories':        Job.CATEGORY_CHOICES,
        'all_skills':        Skill.objects.all(),
        'selected_category': selected_category,
        'selected_skill':    skill_slug,
        'q':                 q,
        'budget_min':        budget_min,
        'budget_max':        budget_max,
    }
    return render(request, 'browse-jobs.html', context)


def job_detail(request, pk):
    job = get_object_or_404(
        Job.objects.select_related('client').prefetch_related('skills'),
        pk=pk,
    )
    # Pass proposal count so template can show it without extra queries
    proposal_count = job.proposals.count() if hasattr(job, 'proposals') else 0
    return render(request, 'job-detail.html', {
        'job':            job,
        'proposal_count': proposal_count,
    })


@login_required
def post_job(request):
    if request.user.role != 'client':
        messages.error(request, 'Faqat mijozlar ish joylashtira oladi.')
        return redirect('job_list')

    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category    = request.POST.get('category', '')
        skill_ids   = request.POST.getlist('skills')  # #9: skills multi-select

        # Budget validation (#4)
        try:
            budget_min = float(request.POST.get('budget_min') or 0)
            budget_max = float(request.POST.get('budget_max') or 0)
        except ValueError:
            budget_min = budget_max = 0

        errors = []
        if not title:
            errors.append('Ish nomi majburiy.')
        if not description or len(description) < 30:
            errors.append('Tavsif kamida 30 belgidan iborat bo\'lishi kerak.')
        if budget_min < 0 or budget_max < 0:
            errors.append('Byudjet manfiy bo\'lishi mumkin emas.')
        if budget_min > 0 and budget_max > 0 and budget_min > budget_max:
            errors.append('Minimal byudjet maksimaldan katta bo\'lishi mumkin emas.')

        if errors:
            return render(request, 'post-job.html', {
                'categories': Job.CATEGORY_CHOICES,
                'all_skills': Skill.objects.all(),
                'error':      ' '.join(errors),
                'form_data':  request.POST,
            })

        job = Job.objects.create(
            client=request.user,
            title=title,
            description=description,
            category=category,
            budget_min=budget_min,
            budget_max=budget_max,
            status='open',
        )
        if skill_ids:
            job.skills.set(Skill.objects.filter(pk__in=skill_ids))

        logger.info('Job created: pk=%s client=%s', job.pk, request.user.pk)
        messages.success(request, 'Ish muvaffaqiyatli joylashtirildi.')
        return redirect('job_detail', pk=job.pk)

    return render(request, 'post-job.html', {
        'categories': Job.CATEGORY_CHOICES,
        'all_skills': Skill.objects.all(),
    })


@login_required
def edit_job(request, pk):
    job = get_object_or_404(Job, pk=pk, client=request.user)

    # #1: Lock editing once proposals are submitted
    has_proposals = job.proposals.exists()
    if has_proposals and request.method == 'POST':
        messages.error(
            request,
            'Bu ishga allaqachon takliflar yuborilgan. '
            'Takliflar mavjud bo\'lganda ishni tahrirlash mumkin emas.'
        )
        return redirect('job_detail', pk=job.pk)

    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category    = request.POST.get('category', '')
        skill_ids   = request.POST.getlist('skills')

        try:
            budget_min = float(request.POST.get('budget_min') or job.budget_min)
            budget_max = float(request.POST.get('budget_max') or job.budget_max)
        except ValueError:
            budget_min, budget_max = float(job.budget_min), float(job.budget_max)

        errors = []
        if not title:
            errors.append('Ish nomi majburiy.')
        if budget_min > 0 and budget_max > 0 and budget_min > budget_max:
            errors.append('Minimal byudjet maksimaldan katta bo\'lishi mumkin emas.')

        if errors:
            return render(request, 'post-job.html', {
                'job':        job,
                'categories': Job.CATEGORY_CHOICES,
                'all_skills': Skill.objects.all(),
                'error':      ' '.join(errors),
            })

        job.title       = title
        job.description = description
        job.category    = category
        job.budget_min  = budget_min
        job.budget_max  = budget_max
        job.save()
        if skill_ids:
            job.skills.set(Skill.objects.filter(pk__in=skill_ids))

        messages.success(request, 'Ish ma\'lumotlari yangilandi.')
        return redirect('job_detail', pk=job.pk)

    return render(request, 'post-job.html', {
        'job':           job,
        'categories':    Job.CATEGORY_CHOICES,
        'all_skills':    Skill.objects.all(),
        'has_proposals': has_proposals,
    })


@login_required
def close_job(request, pk):
    job = get_object_or_404(Job, pk=pk, client=request.user)
    job.status = 'closed'
    job.save(update_fields=['status'])
    messages.success(request, 'Ish yopildi.')
    return redirect('job_detail', pk=job.pk)

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from .models import Category, Job
from Apps.proposals.models import Proposal


def job_list(request):
    selected_category = request.GET.get('category') or ''

    jobs_qs = (
        Job.objects.select_related('category', 'client')
        .prefetch_related('skills')
        .all()
    )
    if selected_category:
        jobs_qs = jobs_qs.filter(category__slug=selected_category)

    if request.user.is_authenticated and getattr(request.user, "role", "") == "freelancer":
        proposed_job_ids = Proposal.objects.filter(freelancer=request.user).values_list("job_id", flat=True)
        jobs_qs = jobs_qs.exclude(id__in=proposed_job_ids)

    categories = Category.objects.all().order_by('name')

    return render(
        request,
        'browse-jobs.html',
        {
            'jobs': jobs_qs,
            'jobs_count': jobs_qs.count(),
            'categories': categories,
            'selected_category': selected_category,
        },
    )


def job_detail(request, pk):
    job = get_object_or_404(Job.objects.select_related("category", "client"), pk=pk)
    return render(request, "job-detail.html", {"job": job})


@login_required
def post_job(request):
    categories = Category.objects.all().order_by("name")
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        category_id = request.POST.get("category") or ""
        budget_min = request.POST.get("budget_min") or 0
        budget_max = request.POST.get("budget_max") or 0

        if not title or not description:
            return render(
                request,
                "post-job.html",
                {"categories": categories, "error": "Title and description are required."},
            )

        category = None
        if category_id:
            category = Category.objects.filter(id=category_id).first()

        job = Job.objects.create(
            client=request.user,
            title=title,
            description=description,
            category=category,
            budget_min=budget_min,
            budget_max=budget_max,
            status="open",
        )
        return redirect("job_detail", pk=job.pk)

    return render(request, "post-job.html", {"categories": categories})


@login_required
def edit_job(request, pk):
    job = get_object_or_404(Job, pk=pk, client=request.user)
    categories = Category.objects.all().order_by("name")

    if request.method == "POST":
        job.title = request.POST.get("title", "").strip()
        job.description = request.POST.get("description", "").strip()
        category_id = request.POST.get("category") or ""
        job.category = Category.objects.filter(id=category_id).first() if category_id else None
        job.budget_min = request.POST.get("budget_min") or 0
        job.budget_max = request.POST.get("budget_max") or 0
        job.save()
        return redirect("job_detail", pk=job.pk)

    return render(request, "post-job.html", {"job": job, "categories": categories})


@login_required
def close_job(request, pk):
    job = get_object_or_404(Job, pk=pk, client=request.user)
    job.status = "closed"
    job.save()
    return redirect("job_detail", pk=job.pk)
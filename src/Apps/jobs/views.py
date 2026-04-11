from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from .models import Job
from Apps.proposals.models import Proposal


def job_list(request):
    selected_category = request.GET.get('category') or ''

    jobs = Job.objects.all()

    if selected_category:
        jobs = jobs.filter(category=selected_category)

    if request.user.is_authenticated and request.user.role == "freelancer":
        my_proposals = Proposal.objects.filter(freelancer=request.user)
        proposed_job_ids = []
        for p in my_proposals:
            proposed_job_ids.append(p.job.id)
        jobs = jobs.exclude(id__in=proposed_job_ids)

    context = {
        'jobs': jobs,
        'jobs_count': jobs.count(),
        'categories': Job.CATEGORY_CHOICES,
        'selected_category': selected_category,
    }
    return render(request, 'browse-jobs.html', context)


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    return render(request, "job-detail.html", {"job": job})


@login_required
def post_job(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        category = request.POST.get("category") or ""
        budget_min = request.POST.get("budget_min") or 0
        budget_max = request.POST.get("budget_max") or 0

        if not title or not description:
            context = {
                "categories": Job.CATEGORY_CHOICES,
                "error": "Title and description are required.",
            }
            return render(request, "post-job.html", context)

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

    return render(request, "post-job.html", {"categories": Job.CATEGORY_CHOICES})


@login_required
def edit_job(request, pk):
    job = get_object_or_404(Job, pk=pk, client=request.user)

    if request.method == "POST":
        job.title = request.POST.get("title", "").strip()
        job.description = request.POST.get("description", "").strip()
        job.category = request.POST.get("category") or ""
        job.budget_min = request.POST.get("budget_min") or 0
        job.budget_max = request.POST.get("budget_max") or 0
        job.save()
        return redirect("job_detail", pk=job.pk)

    return render(request, "post-job.html", {"job": job, "categories": Job.CATEGORY_CHOICES})


@login_required
def close_job(request, pk):
    job = get_object_or_404(Job, pk=pk, client=request.user)
    job.status = "closed"
    job.save()
    return redirect("job_detail", pk=job.pk)

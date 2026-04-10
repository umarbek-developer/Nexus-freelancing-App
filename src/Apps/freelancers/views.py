from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from Apps.reviews.models import Review
from .models import FreelancerProfile, PortfolioItem


@login_required
def browse_freelancers(request):
    profiles = (
        FreelancerProfile.objects.select_related("user")
        .prefetch_related("skills")
        .all()
        .order_by("-id")
    )
    return render(request, "Browse-Freelancer.html", {"profiles": profiles})


@login_required
def freelancer_profile(request, pk):
    profile = get_object_or_404(
        FreelancerProfile.objects.select_related("user").prefetch_related("skills"),
        pk=pk,
    )
    portfolio = PortfolioItem.objects.filter(freelancer=profile.user).order_by("-created_at")
    reviews = Review.objects.filter(reviewee=profile.user).select_related("reviewer").order_by("-created_at")
    return render(
        request,
        "freelancer-profile.html",
        {"profile": profile, "portfolio": portfolio, "reviews": reviews},
    )
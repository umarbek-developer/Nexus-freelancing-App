"""
Freelancer views.

Features:
  #10 — portfolio CRUD (add / delete portfolio items)
  #12 — average rating computed and displayed on profile
  #17 — select_related / prefetch_related on all queries
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.shortcuts import render, get_object_or_404, redirect

from Apps.reviews.models import Review
from .models import FreelancerProfile, PortfolioItem

logger = logging.getLogger(__name__)


@login_required
def browse_freelancers(request):
    profiles = (
        FreelancerProfile.objects
        .select_related('user')          # #17: avoid N+1 on user lookup
        .prefetch_related('skills')
        .filter(availability=True)
        .annotate(avg_rating=Avg('user__reviews_received__rating'))  # #12
        .order_by('-avg_rating')
    )
    return render(request, 'Browse-Freelancer.html', {'profiles': profiles})


@login_required
def freelancer_profile(request, pk):
    profile = get_object_or_404(
        FreelancerProfile.objects.select_related('user').prefetch_related('skills'),
        pk=pk,
    )
    portfolio = (
        PortfolioItem.objects
        .filter(freelancer=profile.user)
        .order_by('-created_at')
    )
    reviews    = Review.objects.filter(reviewee=profile.user).select_related('reviewer')
    # #12: aggregate average rating
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']

    return render(request, 'freelancer-profile.html', {
        'profile':    profile,
        'portfolio':  portfolio,
        'reviews':    reviews,
        'avg_rating': round(avg_rating, 1) if avg_rating else None,
    })


# ── Feature #10: Portfolio management ────────────────────────────────────────

@login_required
def portfolio_add(request):
    """Freelancer adds a new portfolio item."""
    if request.user.role != 'freelancer':
        messages.error(request, 'Faqat freelancerlar portfolio qo\'sha oladi.')
        return redirect('dashboard')

    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        image       = request.FILES.get('image')

        if not title:
            messages.error(request, 'Portfolio nomi majburiy.')
            return render(request, 'portfolio-form.html')

        PortfolioItem.objects.create(
            freelancer=request.user,
            title=title,
            description=description,
            image=image,
        )
        logger.info('Portfolio item added: user=%s title=%s', request.user.pk, title)
        messages.success(request, 'Portfolio elementi qo\'shildi.')
        try:
            profile = request.user.freelancerprofile
            return redirect('freelancer_profile', pk=profile.pk)
        except FreelancerProfile.DoesNotExist:
            return redirect('dashboard')

    return render(request, 'portfolio-form.html')


@login_required
def portfolio_delete(request, pk):
    """Freelancer deletes their own portfolio item."""
    item = get_object_or_404(PortfolioItem, pk=pk, freelancer=request.user)

    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Portfolio elementi o\'chirildi.')

    try:
        profile = request.user.freelancerprofile
        return redirect('freelancer_profile', pk=profile.pk)
    except FreelancerProfile.DoesNotExist:
        return redirect('dashboard')

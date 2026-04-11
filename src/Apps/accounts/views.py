from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import User
from .forms import ProfileForm
from Apps.jobs.models import Job
from Apps.contracts.models import Contract
from Apps.proposals.models import Proposal


def landing_page(request):
    return render(request, 'landing_page.html')


def csrf_failure(request, reason=""):
    messages.error(request, "Xavfsizlik tekshiruvi xatosi. Qayta urinib ko'ring.")
    return redirect("login")


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        role = request.POST.get("role", User.CLIENT)

        if not username or not password1:
            messages.error(request, "Foydalanuvchi nomi va parol majburiy.")
        elif password1 != password2:
            messages.error(request, "Parollar mos kelmadi.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Bu foydalanuvchi nomi band.")
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                role=role,
            )
            auth_login(request, user)
            return redirect("dashboard")

    return render(request, "Registration.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Foydalanuvchi nomi yoki parol notoʻgʻri.")
        else:
            auth_login(request, user)
            return redirect("dashboard")

    return render(request, "Login.html")


def logout_view(request):
    auth_logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    if request.user.role == User.FREELANCER:
        return redirect("freelancer_dashboard")
    return redirect("client_dashboard")


@login_required
def client_dashboard(request):
    my_jobs = Job.objects.filter(client=request.user)

    active_jobs_count = 0
    for job in my_jobs:
        if job.status not in ["completed", "closed"]:
            active_jobs_count += 1

    my_contracts = Contract.objects.filter(client=request.user)
    spent_total = 0
    for c in my_contracts:
        spent_total += c.amount

    active_projects_this_month = 0
    for contract in my_contracts:
        if contract.status == "active":
            active_projects_this_month += 1

    pending_proposals_count = 0
    for job in my_jobs:
        pending_proposals_count += Proposal.objects.filter(job=job, status="pending").count()

    context = {
        "active_jobs_count": active_jobs_count,
        "spent_total": spent_total,
        "active_projects_this_month": active_projects_this_month,
        "pending_proposals_count": pending_proposals_count,
    }
    return render(request, "client-dashboard.html", context)


@login_required
def freelancer_dashboard(request):
    my_contracts = Contract.objects.filter(freelancer=request.user)
    my_proposals = Proposal.objects.filter(freelancer=request.user)

    contract_total = 0
    for c in my_contracts:
        contract_total += c.amount

    proposal_total = 0
    for p in my_proposals:
        if p.status != "rejected":
            proposal_total += p.proposed_rate

    earned_total = contract_total + proposal_total

    active_contracts_count = 0
    for c in my_contracts:
        if c.status == "active":
            active_contracts_count += 1

    active_proposals_count = 0
    for p in my_proposals:
        if p.status != "rejected":
            active_proposals_count += 1

    context = {
        "earned_total": earned_total,
        "contract_total": contract_total,
        "proposal_total": proposal_total,
        "active_contracts_count": active_contracts_count,
        "active_proposals_count": active_proposals_count,
    }
    return render(request, "freelancer-dashboard.html", context)


@login_required
def profile_settings(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil yangilandi.")
            return redirect("dashboard")
        messages.error(request, "Saqlashda xatolik bor.")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "profile-settings.html", {"form": form})

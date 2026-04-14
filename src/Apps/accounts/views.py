from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import User
from .forms import ProfileForm
from Apps.jobs.models import Job
from Apps.contracts.models import Contract
from Apps.proposals.models import Proposal
from Apps.wallet.models import Wallet


def landing_page(request):
    return render(request, 'landing_page.html')


def csrf_failure(request, reason=""):
    messages.error(request, "Xavfsizlik tekshiruvi xatosi. Qayta urinib ko'ring.")
    return redirect("login")


# ── Role selection ──────────────────────────────────────────

def register_role_select(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "register-role.html")


# ── Client registration ─────────────────────────────────────

def register_client(request):
    if request.user.is_authenticated:
        return redirect("client_dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email    = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        if not username or not password1:
            messages.error(request, "Foydalanuvchi nomi va parol majburiy.")
        elif password1 != password2:
            messages.error(request, "Parollar mos kelmadi.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Bu foydalanuvchi nomi band.")
        else:
            user = User.objects.create_user(
                username=username, email=email,
                password=password1, role=User.CLIENT,
            )
            auth_login(request, user)
            messages.success(request, f"Xush kelibsiz, {username}! Mijoz akkauntingiz yaratildi.")
            return redirect("client_dashboard")

    return render(request, "register-client.html")


# ── Freelancer registration ─────────────────────────────────

def register_freelancer(request):
    if request.user.is_authenticated:
        return redirect("freelancer_dashboard")
    if request.method == "POST":
        username  = request.POST.get("username", "").strip()
        email     = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        title     = request.POST.get("title", "").strip() or "Freelancer"

        if not username or not password1:
            messages.error(request, "Foydalanuvchi nomi va parol majburiy.")
        elif password1 != password2:
            messages.error(request, "Parollar mos kelmadi.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Bu foydalanuvchi nomi band.")
        else:
            user = User.objects.create_user(
                username=username, email=email,
                password=password1, role=User.FREELANCER,
            )
            # Auto-create freelancer profile so they appear in browse
            from Apps.freelancers.models import FreelancerProfile
            FreelancerProfile.objects.create(user=user, title=title)
            auth_login(request, user)
            messages.success(request, f"Xush kelibsiz, {username}! Freelancer akkauntingiz yaratildi.")
            return redirect("freelancer_dashboard")

    return render(request, "register-freelancer.html")


# ── Universal login (middleware redirects here) ─────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
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


# ── Client login ────────────────────────────────────────────

def login_client(request):
    if request.user.is_authenticated:
        return redirect("client_dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Foydalanuvchi nomi yoki parol notoʻgʻri.")
        elif user.role != User.CLIENT:
            messages.error(request, "Bu akkaunt Freelancer hisoblanadi. Freelancer sahifasidan kiring.")
        else:
            auth_login(request, user)
            return redirect("client_dashboard")
    return render(request, "login-client.html")


# ── Freelancer login ────────────────────────────────────────

def login_freelancer(request):
    if request.user.is_authenticated:
        return redirect("freelancer_dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Foydalanuvchi nomi yoki parol notoʻgʻri.")
        elif user.role != User.FREELANCER:
            messages.error(request, "Bu akkaunt Mijoz hisoblanadi. Mijoz sahifasidan kiring.")
        else:
            auth_login(request, user)
            return redirect("freelancer_dashboard")
    return render(request, "login-freelancer.html")


def logout_view(request):
    auth_logout(request)
    return redirect("login")


# ── Dashboards ──────────────────────────────────────────────

@login_required
def dashboard(request):
    if request.user.role == User.FREELANCER:
        return redirect("freelancer_dashboard")
    return redirect("client_dashboard")


@login_required
def client_dashboard(request):
    if request.user.role != User.CLIENT:
        return redirect("freelancer_dashboard")

    my_jobs = Job.objects.filter(client=request.user).order_by('-created_at')
    active_jobs_count = my_jobs.exclude(status__in=["completed", "closed"]).count()

    my_contracts = (
        Contract.objects
        .filter(client=request.user)
        .select_related('job', 'freelancer')
        .order_by('-created_at')
    )
    spent_total = sum(c.amount for c in my_contracts)
    active_projects_this_month = my_contracts.filter(status="active").count()

    pending_proposals = (
        Proposal.objects
        .filter(job__in=my_jobs, status="pending")
        .select_related('freelancer', 'job')
        .order_by('-created_at')
    )
    pending_proposals_count = pending_proposals.count()

    context = {
        "active_jobs_count": active_jobs_count,
        "spent_total": spent_total,
        "active_projects_this_month": active_projects_this_month,
        "pending_proposals_count": pending_proposals_count,
        "pending_proposals": pending_proposals,
        "my_contracts": my_contracts,
        "my_jobs": my_jobs,
    }
    return render(request, "client-dashboard.html", context)


@login_required
def freelancer_dashboard(request):
    if request.user.role != User.FREELANCER:
        return redirect("client_dashboard")

    my_contracts = (
        Contract.objects
        .filter(freelancer=request.user)
        .select_related('job', 'client')
        .order_by('-created_at')
    )
    my_proposals = (
        Proposal.objects
        .filter(freelancer=request.user)
        .select_related('job')
        .order_by('-created_at')
    )

    # Wallet: available = real stored balance (credited on contract completion)
    #         pending   = active contracts not yet paid out
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    available_wallet = wallet.balance
    pending_wallet   = sum(c.amount for c in my_contracts if c.status == "active")
    total_wallet     = available_wallet + pending_wallet

    active_contracts_count    = my_contracts.filter(status="active").count()
    pending_proposals_count   = my_proposals.filter(status="pending").count()
    accepted_proposals_count  = my_proposals.filter(status="accepted").count()
    active_proposals_count    = my_proposals.exclude(status="rejected").count()

    context = {
        "available_wallet": available_wallet,
        "pending_wallet": pending_wallet,
        "total_wallet": total_wallet,
        "wallet_transactions": wallet.transactions.all()[:10],
        "active_contracts_count": active_contracts_count,
        "active_proposals_count": active_proposals_count,
        "pending_proposals_count": pending_proposals_count,
        "accepted_proposals_count": accepted_proposals_count,
        "my_contracts": my_contracts,
        "my_proposals": my_proposals,
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

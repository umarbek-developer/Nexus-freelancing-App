"""
DRF API views for the freelancing platform.

Endpoints:
  POST /api/offers/                 → SendOfferView       (freelancer)
  GET  /api/offers/received/        → ReceivedOffersView  (client)
  POST /api/offers/<pk>/accept/     → AcceptOfferView     (client)
  POST /api/offers/<pk>/reject/     → RejectOfferView     (client)
  POST /api/contracts/<pk>/complete/ → CompleteContractView (client)
  GET  /api/wallet/                 → WalletView          (any auth)
  GET  /api/dashboard/client/       → ClientDashboardView  (client)
  GET  /api/dashboard/freelancer/   → FreelancerDashboardView (freelancer)
"""
from django.db import transaction

from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from Apps.contracts.models import Contract
from Apps.jobs.models import Job
from Apps.proposals.models import Proposal
from Apps.wallet.models import Wallet

from .permissions import IsClient, IsFreelancer, IsClientOrFreelancer
from .serializers import (
    ClientDashboardSerializer,
    ContractSerializer,
    FreelancerDashboardSerializer,
    OfferCreateSerializer,
    OfferSerializer,
    WalletSerializer,
)


# ── Offer (Proposal) views ────────────────────────────────────────────────────

class SendOfferView(APIView):
    """POST /api/offers/ — freelancer submits an offer on an open job."""
    permission_classes = [IsFreelancer]

    def post(self, request):
        serializer = OfferCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        proposal = serializer.save()
        return Response(
            OfferSerializer(proposal).data,
            status=status.HTTP_201_CREATED,
        )


class ReceivedOffersView(APIView):
    """GET /api/offers/received/ — client lists offers on their jobs."""
    permission_classes = [IsClient]

    def get(self, request):
        proposals = (
            Proposal.objects
            .filter(job__client=request.user)
            .select_related('job', 'freelancer', 'job__client')
        )
        return Response(OfferSerializer(proposals, many=True).data)


class AcceptOfferView(APIView):
    """
    POST /api/offers/<pk>/accept/ — client accepts one offer.

    Side-effects (atomic):
      1. Proposal → accepted
      2. All other proposals for the same job → rejected
      3. Job status → in_progress
      4. Contract created (or existing returned if somehow already there)
    """
    permission_classes = [IsClient]

    def post(self, request, pk):
        proposal = get_object_or_404(
            Proposal.objects.select_related('job', 'freelancer', 'job__client'),
            pk=pk,
        )

        # Only the job owner may accept
        if proposal.job.client != request.user:
            return Response(
                {'error': 'Siz bu taklifni qabul qila olmaysiz.', 'code': 'forbidden'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if proposal.status == Proposal.ACCEPTED:
            return Response(
                {'error': 'Bu taklif allaqachon qabul qilingan.', 'code': 'already_accepted'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if proposal.status == Proposal.REJECTED:
            return Response(
                {'error': 'Rad etilgan taklifni qabul qilib bo\'lmaydi.', 'code': 'already_rejected'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Accept this proposal
            proposal.status = Proposal.ACCEPTED
            proposal.save(update_fields=['status', 'updated_at'])

            # Reject all other pending proposals for the same job
            Proposal.objects.filter(
                job=proposal.job,
                status=Proposal.PENDING,
            ).exclude(pk=proposal.pk).update(status=Proposal.REJECTED)

            # Move job to in_progress
            Job.objects.filter(pk=proposal.job_id).update(status='in_progress')

            # Create contract (guard against double-accept race)
            contract, _ = Contract.objects.get_or_create(
                job=proposal.job,
                defaults={
                    'client':     proposal.job.client,
                    'freelancer': proposal.freelancer,
                    'amount':     proposal.proposed_rate,
                    'status':     'active',
                },
            )

        return Response(ContractSerializer(contract).data, status=status.HTTP_201_CREATED)


class RejectOfferView(APIView):
    """POST /api/offers/<pk>/reject/ — client rejects a single offer."""
    permission_classes = [IsClient]

    def post(self, request, pk):
        proposal = get_object_or_404(
            Proposal.objects.select_related('job__client'),
            pk=pk,
        )

        if proposal.job.client != request.user:
            return Response(
                {'error': 'Siz bu taklifni rad eta olmaysiz.', 'code': 'forbidden'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if proposal.status != Proposal.PENDING:
            return Response(
                {'error': 'Faqat kutilayotgan takliflarni rad etish mumkin.', 'code': 'invalid_status'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        proposal.status = Proposal.REJECTED
        proposal.save(update_fields=['status', 'updated_at'])
        return Response({'detail': 'Taklif rad etildi.'})


# ── Contract views ────────────────────────────────────────────────────────────

class CompleteContractView(APIView):
    """
    POST /api/contracts/<pk>/complete/ — client marks a contract as completed.

    Side-effects (atomic, row-locked):
      1. Contract → completed
      2. Job → completed
      3. Freelancer wallet credited with contract amount
      4. Transaction record created (inside Wallet.credit())
    """
    permission_classes = [IsClient]

    def post(self, request, pk):
        contract = get_object_or_404(
            Contract.objects.select_related('job', 'freelancer', 'client'),
            pk=pk,
        )

        if contract.client != request.user:
            return Response(
                {'error': 'Siz bu shartnomani yakunlay olmaysiz.', 'code': 'forbidden'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if contract.status == 'completed':
            return Response(
                {'error': 'Bu shartnoma allaqachon yakunlangan.', 'code': 'already_completed'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if contract.status != 'active':
            return Response(
                {'error': 'Faqat faol shartnomalarni yakunlash mumkin.', 'code': 'invalid_status'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Lock wallet row to prevent concurrent balance corruption
            wallet = (
                Wallet.objects
                .select_for_update()
                .get(user=contract.freelancer)
            )

            # Mark contract and job as completed
            Contract.objects.filter(pk=contract.pk).update(status='completed')
            Job.objects.filter(pk=contract.job_id).update(status='completed')

            # Credit the freelancer (also creates Transaction ledger entry)
            wallet.credit(
                amount=contract.amount,
                description=f'Shartnoma #{contract.pk} uchun to\'lov: {contract.job.title}',
            )

        # Re-fetch to reflect updated status
        contract.refresh_from_db()
        return Response(ContractSerializer(contract).data)


# ── Wallet view ───────────────────────────────────────────────────────────────

class WalletView(APIView):
    """GET /api/wallet/ — returns the caller's wallet + transaction history."""
    permission_classes = [IsClientOrFreelancer]

    def get(self, request):
        wallet = get_object_or_404(
            Wallet.objects.prefetch_related('transactions'),
            user=request.user,
        )
        return Response(WalletSerializer(wallet).data)


# ── Dashboard views ───────────────────────────────────────────────────────────

class ClientDashboardView(APIView):
    """GET /api/dashboard/client/ — aggregated data for the client dashboard."""
    permission_classes = [IsClient]

    def get(self, request):
        user = request.user

        pending_offers = (
            Proposal.objects
            .filter(job__client=user, status=Proposal.PENDING)
            .select_related('job', 'freelancer', 'job__client')
        )
        active_contracts = (
            Contract.objects
            .filter(client=user, status='active')
            .select_related('job', 'freelancer', 'client')
        )

        stats = {
            'total_jobs':         Job.objects.filter(client=user).count(),
            'open_jobs':          Job.objects.filter(client=user, status='open').count(),
            'active_contracts':   active_contracts.count(),
            'completed_contracts': Contract.objects.filter(client=user, status='completed').count(),
            'pending_offers':     pending_offers.count(),
        }

        data = {
            'stats':            stats,
            'pending_offers':   pending_offers,
            'active_contracts': active_contracts,
        }
        serializer = ClientDashboardSerializer(data)
        return Response(serializer.data)


class FreelancerDashboardView(APIView):
    """GET /api/dashboard/freelancer/ — aggregated data for the freelancer dashboard."""
    permission_classes = [IsFreelancer]

    def get(self, request):
        user = request.user

        wallet = get_object_or_404(
            Wallet.objects.prefetch_related('transactions'),
            user=user,
        )
        my_contracts = (
            Contract.objects
            .filter(freelancer=user)
            .select_related('job', 'client', 'freelancer')
        )

        stats = {
            'total_proposals':    Proposal.objects.filter(freelancer=user).count(),
            'pending_proposals':  Proposal.objects.filter(freelancer=user, status=Proposal.PENDING).count(),
            'accepted_proposals': Proposal.objects.filter(freelancer=user, status=Proposal.ACCEPTED).count(),
            'active_contracts':   my_contracts.filter(status='active').count(),
            'completed_contracts': my_contracts.filter(status='completed').count(),
        }

        data = {
            'wallet':       wallet,
            'stats':        stats,
            'my_contracts': my_contracts,
        }
        serializer = FreelancerDashboardSerializer(data)
        return Response(serializer.data)

"""
All DRF serializers for the freelancing platform API.
"""
from decimal import Decimal

from rest_framework import serializers

from Apps.accounts.models import User
from Apps.contracts.models import Contract
from Apps.jobs.models import Job
from Apps.proposals.models import Proposal
from Apps.wallet.models import Transaction, Wallet


# ── Lightweight user representation ─────────────────────────────────────────

class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ('id', 'username', 'role')


# ── Job ──────────────────────────────────────────────────────────────────────

class JobBriefSerializer(serializers.ModelSerializer):
    client = UserBriefSerializer(read_only=True)

    class Meta:
        model  = Job
        fields = ('id', 'title', 'description', 'budget_min', 'budget_max',
                  'category', 'status', 'client', 'created_at')


# ── Offer (Proposal) ─────────────────────────────────────────────────────────

class OfferSerializer(serializers.ModelSerializer):
    """Read serializer — returned after create / in list views."""
    freelancer = UserBriefSerializer(read_only=True)
    client     = serializers.SerializerMethodField()
    job        = JobBriefSerializer(read_only=True)

    class Meta:
        model  = Proposal
        fields = ('id', 'job', 'freelancer', 'client',
                  'cover_letter', 'proposed_rate', 'status',
                  'created_at', 'updated_at')
        read_only_fields = fields

    def get_client(self, obj: Proposal):
        return UserBriefSerializer(obj.job.client).data


class OfferCreateSerializer(serializers.ModelSerializer):
    """
    Write serializer — used when a freelancer submits an offer.
    Validates:
      - job exists and is open
      - requester is a freelancer
      - no duplicate offer for this (job, freelancer) pair
      - price is within job budget range
    """
    job_id        = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.filter(status='open'),
        source='job',
        write_only=True,
    )
    proposed_rate = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('1'))
    cover_letter  = serializers.CharField(min_length=20, max_length=3000)

    class Meta:
        model  = Proposal
        fields = ('job_id', 'cover_letter', 'proposed_rate')

    def validate(self, attrs):
        request   = self.context['request']
        job       = attrs['job']
        freelancer = request.user

        # Cannot apply to own job (edge case: client+freelancer double account)
        if job.client == freelancer:
            raise serializers.ValidationError(
                'O\'z ishingizga taklif yuborib bo\'lmaydi.'
            )

        # Duplicate check
        if Proposal.objects.filter(job=job, freelancer=freelancer).exists():
            raise serializers.ValidationError(
                'Siz bu ish uchun allaqachon taklif yuborgansiz.'
            )

        return attrs

    def create(self, validated_data):
        validated_data['freelancer'] = self.context['request'].user
        return super().create(validated_data)


# ── Contract ─────────────────────────────────────────────────────────────────

class ContractSerializer(serializers.ModelSerializer):
    job        = JobBriefSerializer(read_only=True)
    client     = UserBriefSerializer(read_only=True)
    freelancer = UserBriefSerializer(read_only=True)

    class Meta:
        model  = Contract
        fields = ('id', 'job', 'client', 'freelancer',
                  'amount', 'status', 'created_at')
        read_only_fields = fields


# ── Wallet & Transaction ─────────────────────────────────────────────────────

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Transaction
        fields = ('id', 'amount', 'transaction_type', 'description', 'created_at')
        read_only_fields = fields


class WalletSerializer(serializers.ModelSerializer):
    transactions    = TransactionSerializer(many=True, read_only=True)
    pending_balance = serializers.SerializerMethodField()
    owner           = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model  = Wallet
        fields = ('id', 'owner', 'balance', 'pending_balance',
                  'updated_at', 'transactions')
        read_only_fields = fields

    def get_pending_balance(self, obj: Wallet) -> str:
        """Active (not yet completed) contract amounts."""
        total = sum(
            c.amount
            for c in Contract.objects.filter(
                freelancer=obj.user, status='active'
            )
        )
        return str(total)


# ── Dashboard summaries ───────────────────────────────────────────────────────

class ClientDashboardSerializer(serializers.Serializer):
    stats            = serializers.DictField()
    pending_offers   = OfferSerializer(many=True)
    active_contracts = ContractSerializer(many=True)


class FreelancerDashboardSerializer(serializers.Serializer):
    wallet       = WalletSerializer()
    stats        = serializers.DictField()
    my_contracts = ContractSerializer(many=True)

from django.db import models
from django.conf import settings


class Proposal(models.Model):
    # Status constants — use these everywhere instead of raw strings
    PENDING  = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'

    STATUS_CHOICES = [
        (PENDING,  'Pending'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
    ]

    job          = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, related_name='proposals')
    freelancer   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proposals')
    cover_letter = models.TextField()
    proposed_rate = models.DecimalField(max_digits=10, decimal_places=2)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        # One freelancer can submit only one proposal per job
        unique_together = ('job', 'freelancer')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.freelancer.username} → {self.job.title} [{self.status}]'

    @property
    def client(self):
        """Convenience accessor — avoids joining through job every time."""
        return self.job.client

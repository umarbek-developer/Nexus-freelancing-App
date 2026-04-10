from django.db import models
from django.conf import settings


class FreelancerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    skills = models.ManyToManyField('jobs.Skill', blank=True)
    availability = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class PortfolioItem(models.Model):
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='portfolio/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    FREELANCER = 'freelancer'
    CLIENT = 'client'
    ROLE_CHOICES = [
        (FREELANCER, 'Freelancer'),
        (CLIENT, 'Client'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=CLIENT)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.username
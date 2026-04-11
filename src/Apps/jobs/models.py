from django.db import models
from django.conf import settings


class Skill(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
    ]

    CATEGORY_CHOICES = [
        ('web-development', 'Web Development'),
        ('mobile-development', 'Mobile Development'),
        ('ui-ux-design', 'UI/UX Design'),
        ('graphic-design', 'Graphic Design'),
        ('data-science-ai', 'Data Science & AI'),
        ('devops-cloud', 'DevOps & Cloud'),
        ('cybersecurity', 'Cybersecurity'),
        ('content-writing', 'Content Writing'),
        ('digital-marketing', 'Digital Marketing'),
        ('video-animation', 'Video & Animation'),
    ]

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=300)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True)
    skills = models.ManyToManyField(Skill, blank=True)
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

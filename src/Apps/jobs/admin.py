from django.contrib import admin

from .models import Job, Skill


admin.site.register(Skill)
admin.site.register(Job)

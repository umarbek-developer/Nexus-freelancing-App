from django.contrib import admin

from .models import Category, Job, Skill


admin.site.register(Category)
admin.site.register(Skill)
admin.site.register(Job)

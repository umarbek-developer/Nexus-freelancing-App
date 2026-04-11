from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=300)),
                ('description', models.TextField()),
                ('category', models.CharField(blank=True, choices=[('web-development', 'Web Development'), ('mobile-development', 'Mobile Development'), ('ui-ux-design', 'UI/UX Design'), ('graphic-design', 'Graphic Design'), ('data-science-ai', 'Data Science & AI'), ('devops-cloud', 'DevOps & Cloud'), ('cybersecurity', 'Cybersecurity'), ('content-writing', 'Content Writing'), ('digital-marketing', 'Digital Marketing'), ('video-animation', 'Video & Animation')], max_length=50)),
                ('budget_min', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('budget_max', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('status', models.CharField(choices=[('open', 'Open'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('closed', 'Closed')], default='open', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('skills', models.ManyToManyField(blank=True, to='jobs.skill')),
            ],
        ),
    ]

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from Apps.accounts.views import landing_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_page, name='landing_page'),
    path('accounts/', include('Apps.accounts.urls')),
    path('jobs/', include('Apps.jobs.urls')),
    path('freelancers/', include('Apps.freelancers.urls')),
    path('proposals/', include('Apps.proposals.urls')),
    path('contracts/', include('Apps.contracts.urls')),
    path('reviews/', include('Apps.reviews.urls')),
    path('messaging/', include('Apps.messaging.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from Apps.accounts.views import landing_page
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

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

    # Wallet + withdrawals
    path('wallet/', include('Apps.wallet.urls')),

    # REST API
    path('api/', include('Apps.api.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


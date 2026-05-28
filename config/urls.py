from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/users/", include("apps.users.urls")),
    path("api/wallet/", include("apps.wallet.urls")),
    path("api/betting/", include("apps.betting.urls")),
    path("api/audit/", include("apps.audit.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    path("api/responsible-gaming/", include("apps.responsible_gaming.urls")),
]
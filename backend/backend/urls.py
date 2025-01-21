from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from api.views import RecipeViewSet, short_url


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('recipes/<int:pk>/', RecipeViewSet.as_view({'get': 'retrieve'})),
    path('s/<int:pk>/', short_url, name='short_url'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )

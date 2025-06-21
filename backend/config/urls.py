from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

# API URLs
api_urlpatterns = [
    path('core/', include('apps.core.urls')),
    path('downloads/', include('apps.downloads.urls')),
    path('users/', include('apps.users.urls')),
]

urlpatterns = [
    # Admin
    # path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include(api_urlpatterns)),
    
    # API Documentation
    path('api/docs/', TemplateView.as_view(
        template_name='swagger-ui.html',
        extra_context={'schema_url':'openapi-schema'}
    ), name='swagger-ui'),
    
    # Health check
    path('health/', include('apps.core.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.DOWNLOADS_URL, document_root=settings.DOWNLOADS_ROOT)
    
    # Debug toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
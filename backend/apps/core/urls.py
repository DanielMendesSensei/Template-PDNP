from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HealthCheckView.as_view(), name='health_check'),  # Remove 'health/'
    path('status/', views.SystemStatusView.as_view(), name='system_status'),
]

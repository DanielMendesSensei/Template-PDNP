import psutil
import redis
from django.http import JsonResponse
from django.views import View
from django.conf import settings
from celery import current_app
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

class HealthCheckView(View):
    """
    Endpoint de health check para load balancers
    GET /health/
    """
    
    def get(self, request):
        checks = {
            'database': self._check_database(),
            'redis': self._check_redis(),
            'celery': self._check_celery(),
            'disk_space': self._check_disk_space(),
        }
        
        # Determinar status geral
        all_healthy = all(check['healthy'] for check in checks.values())
        status_code = 200 if all_healthy else 503
        
        return JsonResponse({
            'status': 'healthy' if all_healthy else 'unhealthy',
            'checks': checks,
            'timestamp': timezone.now().isoformat(),
        }, status=status_code)
    
    def _check_database(self):
        """Verificar conexão com banco de dados"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {'healthy': True, 'message': 'Database OK'}
        except Exception as e:
            return {'healthy': False, 'message': f'Database Error: {str(e)}'}
    
    def _check_redis(self):
        """Verificar conexão com Redis"""
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 10)
            result = cache.get('health_check')
            if result == 'ok':
                return {'healthy': True, 'message': 'Redis OK'}
            else:
                return {'healthy': False, 'message': 'Redis connection failed'}
        except Exception as e:
            return {'healthy': False, 'message': f'Redis Error: {str(e)}'}
    
    def _check_celery(self):
        """Verificar Celery workers"""
        try:
            inspect = current_app.control.inspect()
            active_workers = inspect.active()
            
            if active_workers:
                worker_count = len(active_workers)
                return {'healthy': True, 'message': f'Celery OK - {worker_count} workers'}
            else:
                return {'healthy': False, 'message': 'No Celery workers active'}
        except Exception as e:
            return {'healthy': False, 'message': f'Celery Error: {str(e)}'}
    
    def _check_disk_space(self):
        """Verificar espaço em disco"""
        try:
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            
            if free_percent > 10:
                return {'healthy': True, 'message': f'Disk OK - {free_percent:.1f}% free'}
            else:
                return {'healthy': False, 'message': f'Low disk space - {free_percent:.1f}% free'}
        except Exception as e:
            return {'healthy': False, 'message': f'Disk check error: {str(e)}'}

class SystemStatusView(View):
    """
    Endpoint para status detalhado do sistema
    GET /api/core/status/
    """
    
    def get(self, request):
        from django.utils import timezone
        
        # Estatísticas básicas
        stats = {
            'timestamp': timezone.now().isoformat(),
            'uptime': self._get_uptime(),
            'system': {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': dict(psutil.virtual_memory()._asdict()),
                'disk': dict(psutil.disk_usage('/')._asdict()),
            },
            'database': self._get_db_stats(),
            'downloads': self._get_download_stats(),
        }
        
        return JsonResponse(stats)
    
    def _get_uptime(self):
        """Obter uptime do sistema"""
        try:
            import time
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            return uptime_seconds
        except:
            return 0
    
    def _get_db_stats(self):
        """Estatísticas do banco de dados"""
        try:
            from apps.downloads.models import DownloadHistory
            from django.contrib.auth.models import User
            
            return {
                'total_users': User.objects.count(),
                'total_downloads': DownloadHistory.objects.count(),
                'active_downloads': DownloadHistory.objects.filter(
                    status__in=['pending', 'downloading', 'processing']
                ).count(),
                'completed_downloads': DownloadHistory.objects.filter(
                    status='completed'
                ).count(),
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_download_stats(self):
        """Estatísticas de downloads"""
        try:
            from apps.downloads.models import DownloadHistory
            from django.utils import timezone
            from django.db.models import Count
            
            today = timezone.now().date()
            
            return {
                'today': DownloadHistory.objects.filter(
                    created_at__date=today
                ).count(),
                'by_status': dict(
                    DownloadHistory.objects.values('status').annotate(
                        count=Count('id')
                    ).values_list('status', 'count')
                ),
                'by_type': dict(
                    DownloadHistory.objects.values('download_type').annotate(
                        count=Count('id')
                    ).values_list('download_type', 'count')
                ),
            }
        except Exception as e:
            return {'error': str(e)}
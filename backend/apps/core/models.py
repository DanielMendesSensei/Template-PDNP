from django.db import models
from django.utils import timezone

class AppSettings(models.Model):
    """Configurações globais da aplicação"""
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'App Setting'
        verbose_name_plural = 'App Settings'
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"
    
    @classmethod
    def get_setting(cls, key: str, default=None):
        """Obter configuração por chave"""
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_setting(cls, key: str, value: str, description: str = ""):
        """Definir configuração"""
        setting, created = cls.objects.get_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )
        if not created:
            setting.value = value
            if description:
                setting.description = description
            setting.save()
        return setting

class SystemStatus(models.Model):
    """Status do sistema para monitoramento"""
    
    STATUS_CHOICES = [
        ('healthy', 'Healthy'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('maintenance', 'Maintenance'),
    ]
    
    component = models.CharField(max_length=50)  # database, redis, celery, etc
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    message = models.TextField(blank=True)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'System Status'
        verbose_name_plural = 'System Status'
        ordering = ['-timestamp']
        get_latest_by = 'timestamp'
    
    def __str__(self):
        return f"{self.component}: {self.status}"
    
    @classmethod
    def update_component_status(cls, component: str, status: str, message: str = "", details: dict = None):
        """Atualizar status de um componente"""
        return cls.objects.create(
            component=component,
            status=status,
            message=message,
            details=details or {}
        )
    
    @classmethod
    def get_latest_status(cls, component: str):
        """Obter último status de um componente"""
        try:
            return cls.objects.filter(component=component).latest()
        except cls.DoesNotExist:
            return None
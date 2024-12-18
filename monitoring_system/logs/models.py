from django.db import models

# Create your models here.
class DeviceInfo(models.Model):
    ip_address = models.CharField(max_length=45, primary_key=True)  # Указываем ip_address как первичный ключ
    cpu_info = models.TextField()
    ram_info = models.TextField()
    disk_space = models.TextField()
    os_info = models.TextField()
    gpu_info = models.TextField()
    type = models.CharField(max_length=10)

    class Meta:
        db_table = 'device_info'
        managed = False

    def __str__(self):
        return f"Device info {self.ip_address}"

class SystemLog(models.Model):
    timestamp = models.DateTimeField()
    ip_address = models.GenericIPAddressField()
    cpu_load = models.FloatField()
    ram_usage = models.FloatField()
    temperature = models.FloatField()
    log_message = models.TextField()

    class Meta:
        db_table = 'system_logs'
        managed = False  # Django не будет пытаться управлять таблицей

    def __str__(self):
        return f"Log {self.timestamp} - {self.ip_address}"


from django.contrib import admin
from .models import SystemLog, DeviceInfo

# Админка для SystemLog
@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'ip_address', 'ram_usage', 'cpu_load', 'log_message', 'temperature')

# Админка для DeviceInfo
@admin.register(DeviceInfo)
class DeviceInfoAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'cpu_info', 'ram_info', 'disk_space', 'os_info', 'gpu_info', 'type')

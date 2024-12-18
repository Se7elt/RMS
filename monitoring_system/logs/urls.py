from django.urls import path
from . import views

urlpatterns = [
    path('', views.logs_and_devices_view, name='logs_and_devices_view'),
    path('device-details/<str:device_id>/', views.device_details, name='device_details'),
    path('metrics/<str:ip_address>/', views.metrics_view, name='metrics_view'),  # Новый маршрут
    path('logs/', views.get_logs, name='get_logs'),
]


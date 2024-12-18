# Generated by Django 5.1.3 on 2024-12-04 15:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('cpu_info', models.CharField(max_length=255)),
                ('ram_info', models.CharField(max_length=255)),
                ('disk_space', models.CharField(max_length=255)),
                ('os_info', models.CharField(max_length=255)),
                ('gpu_info', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='SystemLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('ip_address', models.GenericIPAddressField()),
                ('cpu_load', models.FloatField()),
                ('ram_usage', models.FloatField()),
                ('temperature', models.FloatField()),
                ('log_message', models.TextField()),
            ],
        ),
        migrations.RenameField(
            model_name='log',
            old_name='log_time',
            new_name='timestamp',
        ),
    ]
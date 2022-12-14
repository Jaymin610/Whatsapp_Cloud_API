# Generated by Django 4.1.2 on 2022-12-11 04:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0058_missmatched_temps'),
    ]

    operations = [
        migrations.CreateModel(
            name='SMS_OutBox',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('to_number', models.CharField(max_length=15, null=True)),
                ('message', models.CharField(blank=True, max_length=1000, null=True)),
                ('send_time', models.DateTimeField(null=True)),
                ('status', models.CharField(max_length=10, null=True)),
                ('request', models.CharField(max_length=255, null=True)),
                ('response', models.TextField(null=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='user.user1')),
            ],
        ),
    ]

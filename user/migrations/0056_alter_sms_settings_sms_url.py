# Generated by Django 4.1.2 on 2022-12-06 06:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0055_sms_settings_sms_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sms_settings',
            name='sms_url',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]

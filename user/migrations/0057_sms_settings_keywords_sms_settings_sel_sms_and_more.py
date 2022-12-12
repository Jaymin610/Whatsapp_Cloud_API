# Generated by Django 4.1.2 on 2022-12-06 08:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0056_alter_sms_settings_sms_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='sms_settings',
            name='keywords',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='sms_settings',
            name='sel_sms',
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name='sms_settings',
            name='sel_whatsapp',
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name='sms_settings',
            name='selective',
            field=models.BooleanField(null=True),
        ),
    ]
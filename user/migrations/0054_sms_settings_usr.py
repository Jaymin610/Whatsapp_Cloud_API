# Generated by Django 4.1.2 on 2022-12-06 04:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0053_sms_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='sms_settings',
            name='usr',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='user.user1'),
        ),
    ]

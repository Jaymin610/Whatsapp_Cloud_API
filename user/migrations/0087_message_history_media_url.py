# Generated by Django 4.1.2 on 2022-12-30 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0086_reminder_user_remark'),
    ]

    operations = [
        migrations.AddField(
            model_name='message_history',
            name='media_url',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]
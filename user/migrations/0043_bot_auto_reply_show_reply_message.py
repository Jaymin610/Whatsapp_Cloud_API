# Generated by Django 4.1.2 on 2022-11-16 05:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0042_bot_auto_reply_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='bot_auto_reply',
            name='show_reply_message',
            field=models.CharField(max_length=1000, null=True),
        ),
    ]

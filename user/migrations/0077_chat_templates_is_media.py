# Generated by Django 4.1.2 on 2022-12-22 04:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0076_chat_templates_temp_preview'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat_templates',
            name='is_media',
            field=models.BooleanField(default=0),
        ),
    ]

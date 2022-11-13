# Generated by Django 4.1.2 on 2022-10-12 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0010_outbox_msg_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='data_summary',
            name='Voice_API',
        ),
        migrations.RemoveField(
            model_name='data_summary',
            name='speechFile',
        ),
        migrations.AddField(
            model_name='data_summary',
            name='msg_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]

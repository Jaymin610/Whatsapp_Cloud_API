# Generated by Django 4.1.2 on 2022-11-30 08:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0049_outbox_media_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='outbox',
            name='media_url',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]
